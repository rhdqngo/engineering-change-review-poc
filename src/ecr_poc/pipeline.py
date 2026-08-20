from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime

from .models import (
    CaseDefinition,
    Decision,
    FinalReview,
    FinalStatus,
    PipelineResult,
    RetrievedCandidate,
    ReviewBatch,
    ReviewItem,
    RoleTrace,
    VerificationBatch,
    VerifierVerdict,
)
from .observability import log_event
from .providers import ReviewProvider
from .retrieval import HybridRetriever, candidate_fingerprint


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _same_candidates(
    baseline: Sequence[RetrievedCandidate], proposed: Sequence[RetrievedCandidate]
) -> bool:
    return candidate_fingerprint(baseline) == candidate_fingerprint(proposed)


async def run_case(
    case: CaseDefinition,
    retriever: HybridRetriever,
    provider: ReviewProvider,
    top_k: int,
    *,
    evaluation_run_id: str | None = None,
    role_timeout_seconds: float | None = None,
) -> PipelineResult:
    started_at = _now()
    run_id = evaluation_run_id or str(uuid.uuid4())
    timeout = role_timeout_seconds or float(os.environ.get("ECR_ROLE_TIMEOUT_SECONDS", "120"))
    role_traces: list[RoleTrace] = []
    role_started = time.monotonic()
    try:
        structured_change, analyst_trace = await asyncio.wait_for(
            provider.analyze(case), timeout=timeout
        )
    except Exception as error:
        log_event(
            "role_failed",
            severity="ERROR",
            run_id=run_id,
            case_id=case.id,
            role="change_analyst",
            model=provider.model_name,
            latency_ms=round((time.monotonic() - role_started) * 1000),
            error_type=type(error).__name__,
        )
        raise
    role_traces.append(analyst_trace)
    log_event(
        "role_completed",
        run_id=run_id,
        case_id=case.id,
        role="change_analyst",
        model=provider.model_name,
        latency_ms=round((time.monotonic() - role_started) * 1000),
    )

    # This object is intentionally shared by both arms. A copied/re-ranked list
    # is not created for Proposed.
    candidates = retriever.retrieve(structured_change, top_k, case=case)
    baseline_candidates = candidates
    proposed_candidates = candidates
    if not _same_candidates(baseline_candidates, proposed_candidates):
        raise RuntimeError("Baseline and Proposed candidate fingerprints differ")

    try:
        role_started = time.monotonic()
        review_batch, review_trace = await asyncio.wait_for(
            provider.review(case, structured_change, proposed_candidates), timeout=timeout
        )
        role_traces.append(review_trace)
        log_event(
            "role_completed",
            run_id=run_id,
            case_id=case.id,
            role="engineering_review",
            model=provider.model_name,
            latency_ms=round((time.monotonic() - role_started) * 1000),
        )
    except Exception as error:  # noqa: BLE001 - review failures must fail closed
        review_batch = ReviewBatch(
            reviews=[
                ReviewItem(
                    source_id=candidate.source_id,
                    decision=Decision.INSUFFICIENT_EVIDENCE,
                    short_reason="Engineering Review provider failed; no advice exposed.",
                )
                for candidate in proposed_candidates
            ]
        )
        role_traces.append(
            RoleTrace(
                role="engineering_review",
                provider=provider.name,
                model=provider.model_name,
                raw_output="",
                parsed=review_batch.model_dump(mode="json"),
                error=f"{type(error).__name__}: {error}",
            )
        )
        log_event(
            "role_failed",
            severity="ERROR",
            run_id=run_id,
            case_id=case.id,
            role="engineering_review",
            model=provider.model_name,
            latency_ms=round((time.monotonic() - role_started) * 1000),
            error_type=type(error).__name__,
        )
    candidate_by_id = {candidate.source_id: candidate for candidate in candidates}
    proposal_counts = Counter(item.source_id for item in review_batch.reviews)
    seen: set[str] = set()
    valid_for_verifier: list[ReviewItem] = []
    final_reviews: list[FinalReview] = []

    for proposal in review_batch.reviews:
        seen.add(proposal.source_id)
        if proposal_counts[proposal.source_id] != 1:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.REJECTED_UNSUPPORTED,
                    short_reason=proposal.short_reason,
                    blocked_stage="schema_duplicate_source",
                )
            )
            continue
        candidate = candidate_by_id.get(proposal.source_id)
        if candidate is None:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.REJECTED_UNSUPPORTED,
                    short_reason=proposal.short_reason,
                    blocked_stage="source_not_in_fixed_top_k",
                )
            )
            continue
        if proposal.decision is Decision.REVIEW:
            if not proposal.evidence or proposal.evidence not in candidate.content:
                final_reviews.append(
                    FinalReview(
                        source_id=proposal.source_id,
                        status=FinalStatus.REJECTED_UNSUPPORTED,
                        short_reason=proposal.short_reason,
                        blocked_stage="deterministic_exact_span",
                    )
                )
                continue
            valid_for_verifier.append(proposal)
        elif proposal.decision is Decision.NO_REVIEW:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.NO_REVIEW,
                    short_reason=proposal.short_reason,
                )
            )
        else:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.INSUFFICIENT_EVIDENCE,
                    evidence=proposal.evidence,
                    short_reason=proposal.short_reason,
                )
            )

    for candidate in candidates:
        if candidate.source_id not in seen:
            final_reviews.append(
                FinalReview(
                    source_id=candidate.source_id,
                    status=FinalStatus.REJECTED_UNSUPPORTED,
                    short_reason="Engineering Review returned no decision for this fixed candidate.",
                    blocked_stage="schema_missing_source",
                )
            )

    verification = VerificationBatch(verifications=[])
    if valid_for_verifier:
        try:
            role_started = time.monotonic()
            verification, verifier_trace = await asyncio.wait_for(
                provider.verify(
                    case,
                    structured_change,
                    valid_for_verifier,
                    proposed_candidates,
                ),
                timeout=timeout,
            )
            role_traces.append(verifier_trace)
            log_event(
                "role_completed",
                run_id=run_id,
                case_id=case.id,
                role="evidence_verifier",
                model=provider.model_name,
                latency_ms=round((time.monotonic() - role_started) * 1000),
            )
        except Exception as error:  # noqa: BLE001 - provider failures must fail closed
            role_traces.append(
                RoleTrace(
                    role="evidence_verifier",
                    provider=provider.name,
                    model=provider.model_name,
                    raw_output="",
                    error=f"{type(error).__name__}: {error}",
                )
            )
            log_event(
                "role_failed",
                severity="ERROR",
                run_id=run_id,
                case_id=case.id,
                role="evidence_verifier",
                model=provider.model_name,
                latency_ms=round((time.monotonic() - role_started) * 1000),
                error_type=type(error).__name__,
            )
    else:
        log_event(
            "verifier_skipped",
            run_id=run_id,
            case_id=case.id,
            blocked_stage="no_exact_review_proposals",
        )

    verification_counts = Counter(item.source_id for item in verification.verifications)
    verification_by_id = {item.source_id: item for item in verification.verifications}
    for proposal in valid_for_verifier:
        verdict = verification_by_id.get(proposal.source_id)
        if verification_counts[proposal.source_id] == 1 and verdict and verdict.supported:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.VERIFIED_REVIEW,
                    evidence=proposal.evidence,
                    short_reason=proposal.short_reason,
                    verifier_reason=verdict.reason,
                )
            )
        else:
            final_reviews.append(
                FinalReview(
                    source_id=proposal.source_id,
                    status=FinalStatus.REJECTED_UNSUPPORTED,
                    short_reason=proposal.short_reason,
                    verifier_reason=(
                        "Verifier returned duplicate verdicts"
                        if verification_counts[proposal.source_id] > 1
                        else verdict.reason
                        if verdict
                        else "Verifier returned no verdict"
                    ),
                    blocked_stage="independent_verifier",
                )
            )

    final_reviews.sort(
        key=lambda item: (
            next(
                (
                    candidate.rank
                    for candidate in candidates
                    if candidate.source_id == item.source_id
                ),
                top_k + 1,
            ),
            item.source_id,
        )
    )
    for item in final_reviews:
        if item.status is FinalStatus.VERIFIED_REVIEW:
            verifier_verdict = VerifierVerdict.SUPPORTED
        elif item.blocked_stage == "independent_verifier":
            verifier_verdict = (
                VerifierVerdict.MISSING
                if item.verifier_reason == "Verifier returned no verdict"
                else VerifierVerdict.REJECTED
            )
        else:
            verifier_verdict = VerifierVerdict.NOT_APPLICABLE
        log_event(
            "decision_recorded",
            run_id=run_id,
            case_id=case.id,
            role="evidence_verifier",
            model=provider.model_name,
            source_id=item.source_id,
            decision=item.status,
            verifier_verdict=verifier_verdict,
            blocked_stage=item.blocked_stage,
        )
    candidate_ids = [candidate.source_id for candidate in candidates]
    retrieval_hit = all(
        target in candidate_ids for target in case.expected_review_targets
    )
    fingerprint = candidate_fingerprint(candidates)
    if candidate_ids != [candidate.source_id for candidate in proposed_candidates]:
        raise RuntimeError("Proposed candidate order changed")
    completed_at = _now()
    return PipelineResult(
        run_id=run_id,
        case_id=case.id,
        case_type=case.type,
        scenario=case.scenario,
        provider=provider.name,
        model=provider.model_name,
        embedding_model=retriever.embedder.model_name,
        started_at=started_at,
        completed_at=completed_at,
        structured_change=structured_change,
        candidates=candidates,
        candidate_fingerprint=fingerprint,
        embedding_index_fingerprint=retriever.embedding_index_fingerprint,
        baseline_candidate_source_ids=candidate_ids,
        proposed_candidate_source_ids=candidate_ids,
        proposed_reviews=review_batch.reviews,
        final_reviews=final_reviews,
        role_traces=role_traces,
        expected_review_targets=case.expected_review_targets,
        retrieval_hit=retrieval_hit,
    )


def seal_payload(result: PipelineResult) -> str:
    payload = {
        "case_id": result.case_id,
        "candidate_fingerprint": result.candidate_fingerprint,
        "baseline": result.baseline_candidate_source_ids,
        "proposed": result.proposed_candidate_source_ids,
    }
    value = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
