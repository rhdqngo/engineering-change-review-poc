from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from typing import Protocol, TypeVar

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from pydantic import BaseModel

from .adk_agent.agent import (
    MODEL,
    make_change_analyst,
    make_engineering_reviewer,
    make_evidence_verifier,
)
from .models import (
    ArtifactSpan,
    CaseDefinition,
    Decision,
    ReviewBatch,
    ReviewItem,
    RoleTrace,
    StructuredChange,
    VerificationBatch,
    VerificationItem,
)
from .prompts import PromptBundle

T = TypeVar("T", bound=BaseModel)


class ReviewProvider(Protocol):
    name: str
    model_name: str

    async def analyze(
        self, case: CaseDefinition
    ) -> tuple[StructuredChange, RoleTrace]: ...

    async def review(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[ReviewBatch, RoleTrace]: ...

    async def verify(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        proposals: Sequence[ReviewItem],
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[VerificationBatch, RoleTrace]: ...


class AdkVertexProvider:
    name = "vertex-adk"

    def __init__(
        self, model_name: str = MODEL, prompt_bundle: PromptBundle | None = None
    ) -> None:
        self.model_name = model_name
        self.prompt_bundle = prompt_bundle

    async def _run(self, agent: LlmAgent, prompt: str, schema: type[T]) -> tuple[T, str]:
        runner = InMemoryRunner(agent=agent, app_name=f"ecr_poc_{agent.name}")
        events = await runner.run_debug(
            prompt,
            user_id="evaluation",
            session_id=str(uuid.uuid4()),
            quiet=True,
        )
        outputs: list[str | dict[str, object] | list[object]] = []
        for event in events:
            if event.author != agent.name:
                continue
            if isinstance(event.output, (str, dict, list)):
                outputs.append(event.output)
            if event.content:
                for part in event.content.parts or []:
                    if part.text and not part.thought:
                        outputs.append(part.text)
        if not outputs:
            raise RuntimeError(f"ADK role {agent.name} returned no structured output")
        value = outputs[-1]
        if isinstance(value, str):
            return schema.model_validate_json(value), value
        raw = json.dumps(value, ensure_ascii=False)
        return schema.model_validate(value), raw

    async def analyze(self, case: CaseDefinition) -> tuple[StructuredChange, RoleTrace]:
        prompt = json.dumps({"change_text": case.change_text}, ensure_ascii=False)
        parsed, raw = await self._run(
            make_change_analyst(self.prompt_bundle), prompt, StructuredChange
        )
        return parsed, RoleTrace(
            role="change_analyst",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=parsed.model_dump(mode="json"),
        )

    async def review(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[ReviewBatch, RoleTrace]:
        payload = {
            "change": change.model_dump(mode="json"),
            "fixed_candidates": [candidate.model_dump(mode="json") for candidate in candidates],
        }
        parsed, raw = await self._run(
            make_engineering_reviewer(self.prompt_bundle),
            json.dumps(payload, ensure_ascii=False),
            ReviewBatch,
        )
        return parsed, RoleTrace(
            role="engineering_review",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=parsed.model_dump(mode="json"),
        )

    async def verify(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        proposals: Sequence[ReviewItem],
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[VerificationBatch, RoleTrace]:
        by_id = {candidate.source_id: candidate for candidate in candidates}
        payload = {
            "change": change.model_dump(mode="json"),
            "proposals": [
                {
                    "proposal": proposal.model_dump(mode="json"),
                    "candidate": by_id[proposal.source_id].model_dump(mode="json"),
                }
                for proposal in proposals
            ],
        }
        parsed, raw = await self._run(
            make_evidence_verifier(self.prompt_bundle),
            json.dumps(payload, ensure_ascii=False),
            VerificationBatch,
        )
        return parsed, RoleTrace(
            role="evidence_verifier",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=parsed.model_dump(mode="json"),
        )


class FixtureProvider:
    """Deterministic UI/test fixture. It is never valid evidence for the experiment."""

    name = "fixture-not-llm"
    model_name = "none"

    def __init__(self, inject_unsupported: bool = False) -> None:
        self.inject_unsupported = inject_unsupported

    async def analyze(self, case: CaseDefinition) -> tuple[StructuredChange, RoleTrace]:
        raw = case.change.model_dump_json()
        return case.change, RoleTrace(
            role="change_analyst",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=case.change.model_dump(mode="json"),
        )

    async def review(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[ReviewBatch, RoleTrace]:
        reviews: list[ReviewItem] = []
        for candidate in candidates:
            if candidate.source_id in case.expected_review_targets:
                evidence = next(
                    (line.strip() for line in candidate.content.splitlines() if line.strip()),
                    candidate.content,
                )
                if (
                    case.expected_evidence
                    and case.expected_evidence.source_id == candidate.source_id
                ):
                    evidence = case.expected_evidence.span
                reviews.append(
                    ReviewItem(
                        source_id=candidate.source_id,
                        decision=Decision.REVIEW,
                        evidence=evidence,
                        short_reason="Fixture review for UI and deterministic tests only.",
                    )
                )
            else:
                reviews.append(
                    ReviewItem(
                        source_id=candidate.source_id,
                        decision=Decision.NO_REVIEW,
                        short_reason="Fixture no-review decision.",
                    )
                )
        if self.inject_unsupported and case.id == "DIR-01" and candidates:
            unsupported_index = next(
                (
                    index
                    for index, candidate in enumerate(candidates)
                    if candidate.source_id not in case.expected_review_targets
                ),
                0,
            )
            reviews[unsupported_index] = ReviewItem(
                source_id=candidates[unsupported_index].source_id,
                decision=Decision.REVIEW,
                evidence="THIS SPAN DOES NOT EXIST IN THE NASA SOURCE",
                short_reason="Intentional unsupported fixture used to exercise fail-closed behavior.",
            )
        batch = ReviewBatch(reviews=reviews)
        raw = batch.model_dump_json()
        return batch, RoleTrace(
            role="engineering_review",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=batch.model_dump(mode="json"),
        )

    async def verify(
        self,
        case: CaseDefinition,
        change: StructuredChange,
        proposals: Sequence[ReviewItem],
        candidates: Sequence[ArtifactSpan],
    ) -> tuple[VerificationBatch, RoleTrace]:
        batch = VerificationBatch(
            verifications=[
                VerificationItem(
                    source_id=proposal.source_id,
                    supported=True,
                    reason="Fixture verifier support for UI and deterministic tests only.",
                )
                for proposal in proposals
            ]
        )
        raw = batch.model_dump_json()
        return batch, RoleTrace(
            role="evidence_verifier",
            provider=self.name,
            model=self.model_name,
            raw_output=raw,
            parsed=batch.model_dump(mode="json"),
        )
