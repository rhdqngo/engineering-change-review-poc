from __future__ import annotations

import json
import os
import uuid
from collections.abc import Sequence
from contextlib import aclosing
from typing import Protocol, TypeVar

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel

from .adk_agent.agent import MODEL, make_engineering_reviewer, make_evidence_verifier
from .models import (
    CandidateDecision,
    CandidateDecisionBatch,
    CaseDefinition,
    ClaimVerification,
    ClaimVerificationBatch,
    Decision,
    ImpactType,
    RetrievedCandidate,
    ReviewerClaimDraft,
    RoleTrace,
    ValidatedClaim,
    VerifierVerdict,
)
from .prompts import PromptBundle

T = TypeVar("T", bound=BaseModel)


class ReviewProvider(Protocol):
    name: str
    model_name: str

    async def review(
        self,
        case: CaseDefinition,
        candidates: Sequence[RetrievedCandidate],
        final_docket_fingerprint: str,
    ) -> tuple[CandidateDecisionBatch, RoleTrace]: ...

    async def verify(
        self,
        case: CaseDefinition,
        claims: Sequence[ValidatedClaim],
    ) -> tuple[ClaimVerificationBatch, RoleTrace]: ...


class AdkVertexProvider:
    name = "vertex-adk"

    def __init__(
        self, model_name: str = MODEL, prompt_bundle: PromptBundle | None = None
    ) -> None:
        self.model_name = model_name
        self.prompt_bundle = prompt_bundle

    async def _run(self, agent: LlmAgent, prompt: str, schema: type[T]) -> tuple[T, str]:
        runner = InMemoryRunner(agent=agent, app_name=f"ecr_poc_{agent.name}")
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id="evaluation",
            session_id=str(uuid.uuid4()),
        )
        outputs: list[str | dict[str, object] | list[object]] = []
        async with aclosing(
            runner.run_async(
                user_id="evaluation",
                session_id=session.id,
                new_message=types.UserContent(parts=[types.Part(text=prompt)]),
            )
        ) as events:
            async for event in events:
                if event.author != agent.name or not event.is_final_response():
                    continue
                if event.finish_reason != types.FinishReason.STOP:
                    reason = (
                        event.finish_reason.value
                        if event.finish_reason is not None
                        else "MISSING"
                    )
                    raise RuntimeError(
                        f"ADK role {agent.name} stopped before completion: {reason}"
                    )
                if isinstance(event.output, (str, dict, list)):
                    outputs.append(event.output)
                    continue
                if event.content:
                    text = "".join(
                        part.text
                        for part in event.content.parts or []
                        if part.text and not part.thought
                    )
                    if text:
                        outputs.append(text)
        if len(outputs) != 1:
            raise RuntimeError(
                f"ADK role {agent.name} returned {len(outputs)} final structured outputs"
            )
        value = outputs[0]
        if isinstance(value, str):
            return schema.model_validate_json(value), value
        raw = json.dumps(value, ensure_ascii=False)
        return schema.model_validate(value), raw

    async def review(
        self,
        case: CaseDefinition,
        candidates: Sequence[RetrievedCandidate],
        final_docket_fingerprint: str,
    ) -> tuple[CandidateDecisionBatch, RoleTrace]:
        if case.incoming_artifact is None:
            raise ValueError("Purpose-driven review requires an Incoming Artifact")
        payload = {
            "incoming_artifact": case.incoming_artifact.model_dump(mode="json"),
            "final_docket_fingerprint": final_docket_fingerprint,
            "final_docket": [candidate.model_dump(mode="json") for candidate in candidates],
        }
        parsed, _ = await self._run(
            make_engineering_reviewer(self.prompt_bundle),
            json.dumps(payload, ensure_ascii=False),
            CandidateDecisionBatch,
        )
        return parsed, RoleTrace(
            role="engineering_review",
            provider=self.name,
            model=self.model_name,
            parsed=parsed.model_dump(mode="json"),
        )

    async def verify(
        self,
        case: CaseDefinition,
        claims: Sequence[ValidatedClaim],
    ) -> tuple[ClaimVerificationBatch, RoleTrace]:
        if case.incoming_artifact is None:
            raise ValueError("Purpose-driven verification requires an Incoming Artifact")
        payload = {
            "incoming_artifact": case.incoming_artifact.model_dump(mode="json"),
            "claims": [
                {
                    "claim_id": claim.claim_id,
                    "source_id": claim.source_id,
                    "impact_type": claim.impact_type.value,
                    "impact_claim": claim.impact_claim,
                    "evidence_exact_text": claim.evidence_exact_text,
                    "evidence_start_line": claim.evidence_start_line,
                    "evidence_end_line": claim.evidence_end_line,
                }
                for claim in claims
            ],
        }
        parsed, _ = await self._run(
            make_evidence_verifier(self.prompt_bundle),
            json.dumps(payload, ensure_ascii=False),
            ClaimVerificationBatch,
        )
        return parsed, RoleTrace(
            role="evidence_verifier",
            provider=self.name,
            model=self.model_name,
            parsed=parsed.model_dump(mode="json"),
        )


def _first_exact_line(candidate: RetrievedCandidate) -> tuple[str, int]:
    for offset, line in enumerate(candidate.content.splitlines()):
        if line.strip():
            return line.strip(), candidate.start_line + offset
    return candidate.content, candidate.start_line


class FixtureProvider:
    """Deterministic UI/test fixture. It is never experiment evidence."""

    name = "fixture-not-llm"
    model_name = "none"

    def __init__(
        self,
        inject_unsupported: bool = False,
        live_outcome: str | None = None,
    ) -> None:
        self.inject_unsupported = inject_unsupported
        self.live_outcome = live_outcome or os.environ.get(
            "ECR_LIVE_FIXTURE_OUTCOME", "no_review"
        )
        if self.live_outcome not in {"no_review", "review", "inconclusive", "rejected"}:
            raise ValueError("Unknown live fixture outcome")

    async def review(
        self,
        case: CaseDefinition,
        candidates: Sequence[RetrievedCandidate],
        final_docket_fingerprint: str,
    ) -> tuple[CandidateDecisionBatch, RoleTrace]:
        del final_docket_fingerprint
        decisions: list[CandidateDecision] = []
        unsupported_injected = False
        for index, candidate in enumerate(candidates):
            is_live_review = (
                case.type == "live"
                and self.live_outcome in {"review", "rejected"}
                and index == 0
            )
            if case.type == "live" and self.live_outcome == "inconclusive" and index == 0:
                decisions.append(
                    CandidateDecision(
                        source_id=candidate.source_id,
                        decision=Decision.INSUFFICIENT_EVIDENCE,
                    )
                )
                continue
            inject_invalid_claim = (
                self.inject_unsupported
                and case.id == "DIR-01"
                and not unsupported_injected
                and candidate.source_id not in case.expected_review_targets
            )
            if is_live_review or inject_invalid_claim or candidate.source_id in case.expected_review_targets:
                evidence, line = _first_exact_line(candidate)
                expected = case.evidence_for(candidate.source_id)
                if expected:
                    evidence = expected
                    offset = candidate.content[: candidate.content.index(expected)].count("\n")
                    line = candidate.start_line + offset
                if inject_invalid_claim:
                    evidence = "THIS SPAN DOES NOT EXIST IN THE NASA SOURCE"
                    unsupported_injected = True
                decisions.append(
                    CandidateDecision(
                        source_id=candidate.source_id,
                        decision=Decision.REVIEW,
                        claims=[
                            ReviewerClaimDraft(
                                impact_type=case.impact_type_for(candidate.source_id)
                                if not is_live_review
                                else ImpactType.IMPLEMENTATION_IMPACT,
                                impact_claim=(
                                    "Fixture atomic impact claim for deterministic UI validation."
                                ),
                                evidence_exact_text=evidence,
                                evidence_start_line=line,
                                evidence_end_line=line + evidence.count("\n"),
                            )
                        ],
                    )
                )
            else:
                decisions.append(
                    CandidateDecision(
                        source_id=candidate.source_id,
                        decision=Decision.NO_REVIEW,
                    )
                )
        batch = CandidateDecisionBatch(decisions=decisions)
        return batch, RoleTrace(
            role="engineering_review",
            provider=self.name,
            model=self.model_name,
            parsed=batch.model_dump(mode="json"),
        )

    async def verify(
        self,
        case: CaseDefinition,
        claims: Sequence[ValidatedClaim],
    ) -> tuple[ClaimVerificationBatch, RoleTrace]:
        verdict = (
            VerifierVerdict.REJECTED
            if case.type == "live" and self.live_outcome == "rejected"
            else VerifierVerdict.SUPPORTED
        )
        batch = ClaimVerificationBatch(
            verifications=[
                ClaimVerification(
                    claim_id=claim.claim_id,
                    verdict=verdict,
                    reason="Fixture verdict for deterministic tests and UI states only.",
                )
                for claim in claims
            ]
        )
        return batch, RoleTrace(
            role="evidence_verifier",
            provider=self.name,
            model=self.model_name,
            parsed=batch.model_dump(mode="json"),
        )
