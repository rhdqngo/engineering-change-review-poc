from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import (
    CandidateDecisionBatch,
    CandidateFinalStatus,
    CandidateReviewResult,
    Decision,
    RetrievedCandidate,
    ValidatedClaim,
)


@dataclass
class ValidationResult:
    valid_claims: list[ValidatedClaim]
    candidate_results: dict[str, CandidateReviewResult]
    decisions_by_source: dict[str, Decision]
    global_blocked: bool


def validate_candidate_decisions(
    batch: CandidateDecisionBatch,
    final_docket: list[RetrievedCandidate],
) -> ValidationResult:
    candidates = {candidate.source_id: candidate for candidate in final_docket}
    counts = Counter(decision.source_id for decision in batch.decisions)
    decisions_by_source: dict[str, Decision] = {}
    blocked: dict[str, list[str]] = defaultdict(list)
    valid_claims: list[ValidatedClaim] = []
    global_blocked = any(source_id not in candidates for source_id in counts)

    for candidate in final_docket:
        source_id = candidate.source_id
        matching = [
            decision for decision in batch.decisions if decision.source_id == source_id
        ]
        if not matching:
            blocked[source_id].append("schema_missing_source")
            continue
        if len(matching) != 1:
            blocked[source_id].append("schema_duplicate_source")
            continue
        decision = matching[0]
        decisions_by_source[source_id] = decision.decision
        if decision.decision is not Decision.REVIEW:
            continue
        candidate_lines = candidate.content.splitlines()
        for ordinal, draft in enumerate(decision.claims, start=1):
            stage: str | None = None
            if (
                draft.evidence_start_line < candidate.start_line
                or draft.evidence_end_line > candidate.end_line
            ):
                stage = "deterministic_line_range"
            else:
                relative_start = draft.evidence_start_line - candidate.start_line
                relative_end = draft.evidence_end_line - candidate.start_line + 1
                selected = "\n".join(candidate_lines[relative_start:relative_end])
                if draft.evidence_exact_text not in selected:
                    stage = "deterministic_exact_span"
            if stage is not None:
                blocked[source_id].append(stage)
                continue
            valid_claims.append(
                ValidatedClaim(
                    claim_id=f"CLM-{candidate.rank:02d}-{ordinal:02d}",
                    source_id=source_id,
                    final_rank=candidate.rank,
                    impact_type=draft.impact_type,
                    impact_claim=draft.impact_claim,
                    evidence_exact_text=draft.evidence_exact_text,
                    evidence_start_line=draft.evidence_start_line,
                    evidence_end_line=draft.evidence_end_line,
                )
            )

    results: dict[str, CandidateReviewResult] = {}
    for candidate in final_docket:
        source_id = candidate.source_id
        stages = blocked[source_id]
        candidate_decision = decisions_by_source.get(source_id)
        if stages:
            status = CandidateFinalStatus.BLOCKED
        elif candidate_decision is Decision.NO_REVIEW:
            status = CandidateFinalStatus.NO_REVIEW
        elif candidate_decision is Decision.INSUFFICIENT_EVIDENCE:
            status = CandidateFinalStatus.INSUFFICIENT_EVIDENCE
        else:
            # REVIEW is finalized after independent claim verification.
            status = CandidateFinalStatus.BLOCKED
        results[source_id] = CandidateReviewResult(
            source_id=source_id,
            status=status,
            blocked_count=len(stages),
            blocked_stages=list(dict.fromkeys(stages)),
        )
    return ValidationResult(
        valid_claims=valid_claims,
        candidate_results=results,
        decisions_by_source=decisions_by_source,
        global_blocked=global_blocked,
    )
