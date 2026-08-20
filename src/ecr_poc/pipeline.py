from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime

from .claim_validation import validate_candidate_decisions
from .models import (
    CandidateDecision,
    CandidateDecisionBatch,
    CandidateFinalStatus,
    CaseDefinition,
    ClaimVerification,
    ClaimVerificationBatch,
    Decision,
    FinalReview,
    FinalStatus,
    OverallReviewStatus,
    PipelineResult,
    RoleTrace,
    VerifiedClaim,
    VerifierVerdict,
)
from .observability import log_event
from .providers import ReviewProvider
from .retrieval import FINAL_K, HybridRetriever


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def run_case(
    case: CaseDefinition,
    retriever: HybridRetriever,
    provider: ReviewProvider,
    top_k: int = FINAL_K,
    *,
    evaluation_run_id: str | None = None,
    role_timeout_seconds: float | None = None,
) -> PipelineResult:
    if case.incoming_artifact is None:
        raise ValueError("Purpose-driven v6 requires an Incoming Artifact")
    if top_k != FINAL_K:
        raise ValueError("Purpose-driven v6 Final Review Docket must contain Top-10")
    started_at = _now()
    run_id = evaluation_run_id or str(uuid.uuid4())
    timeout = role_timeout_seconds or float(os.environ.get("ECR_ROLE_TIMEOUT_SECONDS", "120"))
    retrieval = retriever.retrieve(case.incoming_artifact, final_k=top_k)
    candidates = retrieval.final_docket
    role_traces: list[RoleTrace] = []
    reviewer_failed = False

    role_started = time.monotonic()
    try:
        decision_batch, review_trace = await asyncio.wait_for(
            provider.review(
                case,
                candidates,
                retrieval.summary.final_docket_fingerprint,
            ),
            timeout=timeout,
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
    except Exception as error:  # noqa: BLE001 - reviewer failures fail closed
        reviewer_failed = True
        decision_batch = CandidateDecisionBatch(
            decisions=[
                CandidateDecision(
                    source_id=candidate.source_id,
                    decision=Decision.INSUFFICIENT_EVIDENCE,
                )
                for candidate in candidates
            ]
        )
        role_traces.append(
            RoleTrace(
                role="engineering_review",
                provider=provider.name,
                model=provider.model_name,
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

    validation = validate_candidate_decisions(decision_batch, candidates)
    if reviewer_failed:
        for result in validation.candidate_results.values():
            result.status = CandidateFinalStatus.BLOCKED
            result.blocked_count += 1
            result.blocked_stages.append("engineering_review_provider")

    verification_batch = ClaimVerificationBatch(verifications=[])
    verifier_failed = False
    if validation.valid_claims and not reviewer_failed:
        role_started = time.monotonic()
        try:
            verification_batch, verifier_trace = await asyncio.wait_for(
                provider.verify(case, validation.valid_claims),
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
        except Exception as error:  # noqa: BLE001 - verifier failures fail closed
            verifier_failed = True
            role_traces.append(
                RoleTrace(
                    role="evidence_verifier",
                    provider=provider.name,
                    model=provider.model_name,
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

    verification_counts = Counter(
        verification.claim_id for verification in verification_batch.verifications
    )
    verification_by_id = {
        verification.claim_id: verification
        for verification in verification_batch.verifications
    }
    claims_by_source = defaultdict(list)
    for claim in validation.valid_claims:
        claims_by_source[claim.source_id].append(claim)

    effective_verifications: list[ClaimVerification] = []
    for candidate in candidates:
        result = validation.candidate_results[candidate.source_id]
        decision = validation.decisions_by_source.get(candidate.source_id)
        if decision is not Decision.REVIEW or reviewer_failed:
            continue
        for claim in claims_by_source[candidate.source_id]:
            verification = verification_by_id.get(claim.claim_id)
            if (
                verifier_failed
                or verification_counts[claim.claim_id] != 1
                or verification is None
            ):
                result.blocked_count += 1
                result.blocked_stages.append(
                    "evidence_verifier_provider"
                    if verifier_failed
                    else "verifier_duplicate_verdict"
                    if verification_counts[claim.claim_id] > 1
                    else "verifier_missing_verdict"
                )
                result.verifier_verdicts.append(VerifierVerdict.MISSING)
                effective_verifications.append(
                    ClaimVerification(
                        claim_id=claim.claim_id,
                        verdict=VerifierVerdict.MISSING,
                        reason="Verifier verdict unavailable; claim withheld.",
                    )
                )
                continue
            effective_verifications.append(verification)
            result.verifier_verdicts.append(verification.verdict)
            if verification.verdict is VerifierVerdict.SUPPORTED:
                result.verified_claims.append(
                    VerifiedClaim(
                        claim_id=claim.claim_id,
                        source_id=claim.source_id,
                        impact_type=claim.impact_type,
                        impact_claim=claim.impact_claim,
                        evidence_exact_text=claim.evidence_exact_text,
                        evidence_start_line=claim.evidence_start_line,
                        evidence_end_line=claim.evidence_end_line,
                        verifier_reason=verification.reason,
                    )
                )

        if result.verified_claims:
            result.status = CandidateFinalStatus.VERIFIED_REVIEW
        elif result.blocked_count:
            result.status = CandidateFinalStatus.BLOCKED
        elif claims_by_source[candidate.source_id] and all(
            verdict is VerifierVerdict.REJECTED
            for verdict in result.verifier_verdicts
        ):
            result.status = CandidateFinalStatus.NO_SUPPORTED_CLAIM
        else:
            result.status = CandidateFinalStatus.BLOCKED
            result.blocked_count += 1
            result.blocked_stages.append("no_valid_review_claim")

    candidate_results = [
        validation.candidate_results[candidate.source_id] for candidate in candidates
    ]
    has_verified = any(
        result.status is CandidateFinalStatus.VERIFIED_REVIEW
        for result in candidate_results
    )
    has_inconclusive = (
        validation.global_blocked
        or any(trace.error for trace in role_traces)
        or any(
            result.status
            in {CandidateFinalStatus.BLOCKED, CandidateFinalStatus.INSUFFICIENT_EVIDENCE}
            for result in candidate_results
        )
    )
    if has_verified:
        overall_status = OverallReviewStatus.REVIEW_REQUIRED
    elif has_inconclusive:
        overall_status = OverallReviewStatus.INCONCLUSIVE
    else:
        overall_status = OverallReviewStatus.NO_SUPPORTED_REVIEW
    partial = has_verified and has_inconclusive

    for result in candidate_results:
        log_event(
            "decision_recorded",
            run_id=run_id,
            case_id=case.id,
            role="evidence_verifier",
            model=provider.model_name,
            source_id=result.source_id,
            decision=result.status,
            verifier_verdict=(
                VerifierVerdict.SUPPORTED
                if result.verified_claims
                else result.verifier_verdicts[0]
                if result.verifier_verdicts
                else None
            ),
            blocked_stage=result.blocked_stages[0] if result.blocked_stages else None,
        )
        for verified_claim in result.verified_claims:
            log_event(
                "verified_claim_recorded",
                run_id=run_id,
                case_id=case.id,
                source_id=result.source_id,
                claim_id=verified_claim.claim_id,
                verifier_verdict=VerifierVerdict.SUPPORTED,
            )

    candidate_ids = [candidate.source_id for candidate in candidates]
    retrieval_hit = all(
        target in candidate_ids for target in case.expected_review_targets
    )
    legacy_final: list[FinalReview] = []
    for result in candidate_results:
        if result.status is CandidateFinalStatus.VERIFIED_REVIEW:
            first = result.verified_claims[0]
            legacy_final.append(
                FinalReview(
                    source_id=result.source_id,
                    status=FinalStatus.VERIFIED_REVIEW,
                    evidence=first.evidence_exact_text,
                    short_reason=first.impact_claim,
                    verifier_reason=first.verifier_reason,
                )
            )
        elif result.status is CandidateFinalStatus.NO_REVIEW:
            legacy_final.append(
                FinalReview(
                    source_id=result.source_id,
                    status=FinalStatus.NO_REVIEW,
                    short_reason="No review need proposed for this Final Docket candidate.",
                )
            )
        elif result.status is CandidateFinalStatus.INSUFFICIENT_EVIDENCE:
            legacy_final.append(
                FinalReview(
                    source_id=result.source_id,
                    status=FinalStatus.INSUFFICIENT_EVIDENCE,
                    short_reason="Reviewer reported insufficient evidence.",
                )
            )
        else:
            legacy_final.append(
                FinalReview(
                    source_id=result.source_id,
                    status=FinalStatus.REJECTED_UNSUPPORTED,
                    short_reason="No unsupported claim or evidence is exposed.",
                    blocked_stage=(
                        result.blocked_stages[0]
                        if result.blocked_stages
                        else "independent_verifier_rejected"
                    ),
                )
            )

    return PipelineResult(
        run_id=run_id,
        case_id=case.id,
        case_type=case.type,
        scenario=case.scenario,
        provider=provider.name,
        model=provider.model_name,
        embedding_model=retriever.embedder.model_name,
        started_at=started_at,
        completed_at=_now(),
        candidates=candidates,
        candidate_fingerprint=retrieval.summary.final_docket_fingerprint,
        embedding_index_fingerprint=retriever.embedding_index_fingerprint,
        identifier_index_fingerprint=retriever.identifier_index_fingerprint,
        query_processing=retrieval.query_processing,
        retrieval=retrieval.summary,
        candidate_decisions=decision_batch.decisions,
        claim_verifications=effective_verifications,
        candidate_results=candidate_results,
        role_traces=role_traces,
        expected_review_targets=case.expected_review_targets,
        expected_claims=case.expected_claims,
        broad_candidate_source_ids=[
            candidate.source_id for candidate in retrieval.broad_candidates
        ],
        expanded_candidate_source_ids=[
            candidate.source_id for candidate in retrieval.expanded_candidates
        ],
        retrieval_hit=retrieval_hit,
        incoming_artifact=case.incoming_artifact,
        overall_status=overall_status,
        partial=partial,
        baseline_candidate_source_ids=candidate_ids,
        proposed_candidate_source_ids=candidate_ids,
        final_reviews=legacy_final,
    )


def seal_payload(result: PipelineResult) -> str:
    payload = {
        "case_id": result.case_id,
        "final_docket_fingerprint": result.candidate_fingerprint,
        "identifier_index_fingerprint": result.identifier_index_fingerprint,
        "candidate_results": [
            item.model_dump(mode="json") for item in result.candidate_results
        ],
        "overall_status": result.overall_status,
        "partial": result.partial,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
