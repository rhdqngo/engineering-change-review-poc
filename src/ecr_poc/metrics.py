from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from .models import CandidateFinalStatus, FinalStatus, PipelineResult, VerifierVerdict

MUTATION_TYPES = {"direct", "semantic", "cross_artifact"}
CONTROL_TYPES = {"clean", "benign"}


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _mean(total: float, count: int) -> float | None:
    return round(total / count, 6) if count else None


def _v6_group_metrics(results: Sequence[PipelineResult]) -> dict[str, Any]:
    impact = [result for result in results if result.case_type in MUTATION_TYPES]
    controls = [result for result in results if result.case_type in CONTROL_TYPES]
    expected_targets = sum(len(result.expected_review_targets) for result in impact)
    expected_claims = sum(len(result.expected_claims) for result in impact)
    broad_hits = 0
    expansion_gain = 0
    expanded_hits = 0
    final_hits = 0
    broad_complete = 0
    expanded_complete = 0
    final_complete = 0
    target_rank_sum = 0
    reciprocal_rank_sum = 0.0
    proposed_expected_claims: set[tuple[str, str]] = set()
    verified_expected_claims: set[tuple[str, str]] = set()
    unregistered_findings = 0
    verified_claim_total = 0
    proposed_claim_total = 0
    blocked_total = 0
    rejected_total = 0
    expanded_total = 0
    final_total = 0
    verified_docket_total = 0

    def slot_matches(
        source_id: str, impact_type: str, evidence: str, result: PipelineResult
    ) -> str | None:
        for slot in result.expected_claims:
            if slot.source_id != source_id or slot.impact_type.value != impact_type:
                continue
            if any(
                expected in evidence or evidence in expected
                for expected in slot.acceptable_exact_evidence_spans
            ):
                return slot.claim_slot_id
        return None

    for result in results:
        ranks = {candidate.source_id: candidate.rank for candidate in result.candidates}
        broad = set(result.broad_candidate_source_ids)
        expanded = set(result.expanded_candidate_source_ids)
        final = set(ranks)
        verified_claims = [
            claim
            for candidate in result.candidate_results
            for claim in candidate.verified_claims
        ]
        verified_claim_total += len(verified_claims)
        proposed_claim_total += sum(
            len(decision.claims) for decision in result.candidate_decisions
        )
        blocked_total += sum(
            candidate.blocked_count for candidate in result.candidate_results
        )
        rejected_total += sum(
            verification.verdict is VerifierVerdict.REJECTED
            for verification in result.claim_verifications
        )
        expanded_total += (
            result.retrieval.expanded_count
            if result.retrieval is not None
            else len(result.expanded_candidate_source_ids)
        )
        final_total += len(result.candidates)
        verified_docket_total += sum(
            candidate.status is CandidateFinalStatus.VERIFIED_REVIEW
            for candidate in result.candidate_results
        )
        for decision in result.candidate_decisions:
            for claim in decision.claims:
                slot_id = slot_matches(
                    decision.source_id,
                    claim.impact_type.value,
                    claim.evidence_exact_text,
                    result,
                )
                if slot_id is not None:
                    proposed_expected_claims.add((result.case_id, slot_id))
        for verified_claim in verified_claims:
            slot_id = slot_matches(
                verified_claim.source_id,
                verified_claim.impact_type.value,
                verified_claim.evidence_exact_text,
                result,
            )
            if slot_id is None:
                if result.case_type in MUTATION_TYPES:
                    unregistered_findings += 1
            else:
                verified_expected_claims.add((result.case_id, slot_id))
        if result.case_type not in MUTATION_TYPES:
            continue
        expected = set(result.expected_review_targets)
        broad_hits += len(expected & broad)
        expanded_hits += len(expected & expanded)
        final_hits += len(expected & final)
        expansion_gain += len((expected & expanded) - broad)
        broad_complete += expected.issubset(broad)
        expanded_complete += expected.issubset(expanded)
        final_complete += expected.issubset(final)
        retrieved = [target for target in expected if target in ranks]
        target_rank_sum += sum(ranks[target] for target in retrieved)
        reciprocal_rank_sum += sum(1 / ranks[target] for target in retrieved)
    false_alarm_cases = sum(
        any(candidate.verified_claims for candidate in result.candidate_results)
        for result in controls
    )
    return {
        "cases": len(results),
        "impact_cases": len(impact),
        "control_cases": len(controls),
        "broad_retrieval_hit_at_40": {
            "hits": broad_hits,
            "eligible_targets": expected_targets,
            "rate": _safe_rate(broad_hits, expected_targets),
        },
        "relation_expansion_gain": {
            "new_target_hits": expansion_gain,
            "eligible_targets": expected_targets,
            "rate": _safe_rate(expansion_gain, expected_targets),
        },
        "expanded_pool_target_coverage": {
            "hits": expanded_hits,
            "eligible_targets": expected_targets,
            "rate": _safe_rate(expanded_hits, expected_targets),
        },
        "final_docket_hit_at_10": {
            "hits": final_hits,
            "eligible_targets": expected_targets,
            "rate": _safe_rate(final_hits, expected_targets),
        },
        "complete_case_coverage": {
            "broad_hits": broad_complete,
            "expanded_hits": expanded_complete,
            "final_hits": final_complete,
            "eligible_cases": len(impact),
        },
        "final_target_rank": {
            "retrieved_targets": final_hits,
            "mean_rank": _mean(target_rank_sum, final_hits),
            "mean_reciprocal_rank": _mean(reciprocal_rank_sum, final_hits),
        },
        "expected_claim_proposal_recall": {
            "matched": len(proposed_expected_claims),
            "eligible_claims": expected_claims,
            "rate": _safe_rate(len(proposed_expected_claims), expected_claims),
        },
        "verified_expected_claim_recall": {
            "matched": len(verified_expected_claims),
            "eligible_claims": expected_claims,
            "rate": _safe_rate(len(verified_expected_claims), expected_claims),
        },
        "clean_benign_false_alarm": {
            "cases": false_alarm_cases,
            "eligible_controls": len(controls),
            "rate": _safe_rate(false_alarm_cases, len(controls)),
        },
        "claim_counts": {
            "proposed": proposed_claim_total,
            "blocked": blocked_total,
            "rejected": rejected_total,
            "verified": verified_claim_total,
        },
        "selection": {
            "average_expanded_pool_size": _mean(expanded_total, len(results)),
            "average_final_docket_size": _mean(final_total, len(results)),
            "average_verified_docket_size": _mean(
                verified_docket_total, len(results)
            ),
            "candidate_reduction": _safe_rate(
                final_total - verified_docket_total, final_total
            ),
        },
        "unregistered_additional_findings": unregistered_findings,
    }


def _calculate_v6_metrics(results: Sequence[PipelineResult]) -> dict[str, Any]:
    groups: dict[str, list[PipelineResult]] = defaultdict(list)
    for result in results:
        groups[result.case_type].append(result)
    return {
        "definitions": {
            "broad_retrieval_hit_at_40": "Expected target present in deterministic Broad Top-40.",
            "relation_expansion_gain": "Expected target absent from Broad Top-40 but recovered in the expanded pool.",
            "final_docket_hit_at_10": "Expected target present in the immutable Final Top-10 docket.",
            "expected_claim_recall": "Frozen structural claim slots matched by proposed or verified atomic claims.",
            "clean_benign_false_alarm": "Clean or benign case with at least one VERIFIED_REVIEW.",
            "unregistered_additional_findings": "Verified impact claim outside frozen structural slots; not automatically a false positive.",
        },
        "overall": _v6_group_metrics(results),
        "by_type": {
            case_type: _v6_group_metrics(groups.get(case_type, []))
            for case_type in ["direct", "semantic", "cross_artifact", "clean", "benign"]
        },
    }


def calculate_metrics(
    results: Sequence[PipelineResult], *, complete_overall: bool = False
) -> dict[str, Any]:
    if any(result.incoming_artifact is not None for result in results):
        return _calculate_v6_metrics(results)
    groups: dict[str, list[PipelineResult]] = defaultdict(list)
    for result in results:
        groups[result.case_type].append(result)

    by_type: dict[str, dict[str, Any]] = {}
    for case_type in ["direct", "semantic", "cross_artifact", "clean", "benign"]:
        typed = groups.get(case_type, [])
        mutation = case_type in MUTATION_TYPES
        retrieval_hits = sum(result.retrieval_hit for result in typed) if mutation else 0
        retrieval_denominator = len(typed) if mutation else 0
        verified_sets = [
            {
                item.source_id
                for item in result.final_reviews
                if item.status is FinalStatus.VERIFIED_REVIEW
            }
            for result in typed
        ]
        success_flags = [
            result.retrieval_hit
            and set(result.expected_review_targets).issubset(verified)
            for result, verified in zip(typed, verified_sets)
        ]
        llm_successes = sum(success_flags) if mutation else 0
        llm_denominator = retrieval_hits if mutation else 0
        false_alarm_cases = (
            sum(bool(verified) for verified in verified_sets) if case_type in CONTROL_TYPES else 0
        )
        candidate_count = sum(len(result.candidates) for result in typed)
        verified_count = sum(len(verified) for verified in verified_sets)
        blocked_count = sum(
            item.status is FinalStatus.REJECTED_UNSUPPORTED
            for result in typed
            for item in result.final_reviews
        )
        proposed_review_count = sum(
            proposal.decision.value == "REVIEW"
            for result in typed
            for proposal in result.proposed_reviews
        )
        target_retained = (
            sum(
                set(result.expected_review_targets).issubset(verified)
                for result, verified in zip(typed, verified_sets)
            )
            if mutation
            else 0
        )
        evidence_complete = sum(
            bool(item.evidence and item.short_reason)
            for result in typed
            for item in result.final_reviews
            if item.status is FinalStatus.VERIFIED_REVIEW
        )
        by_type[case_type] = {
            "cases": len(typed),
            "retrieval_coverage": {
                "hits": retrieval_hits,
                "eligible": retrieval_denominator,
                "rate": _safe_rate(retrieval_hits, retrieval_denominator),
            },
            "llm_review_success": {
                "successes": llm_successes,
                "eligible_retrieval_hits": llm_denominator,
                "rate": _safe_rate(llm_successes, llm_denominator),
            },
            "false_alarm": {
                "cases": false_alarm_cases,
                "eligible_controls": len(typed) if case_type in CONTROL_TYPES else 0,
                "rate": _safe_rate(
                    false_alarm_cases,
                    len(typed) if case_type in CONTROL_TYPES else 0,
                ),
            },
            "review_selection_added_value": {
                "baseline_candidates": candidate_count,
                "final_verified_reviews": verified_count,
                "candidate_reduction_ratio": _safe_rate(
                    candidate_count - verified_count, candidate_count
                ),
                "expected_target_retained_cases": target_retained,
                "verified_reviews_with_evidence_and_reason": evidence_complete,
            },
            "unsupported_output_blocked": {
                "proposed_reviews": proposed_review_count,
                "blocked": blocked_count,
                "final_verified_reviews": verified_count,
            },
        }

    mutation_results = [result for result in results if result.case_type in MUTATION_TYPES]
    control_results = [result for result in results if result.case_type in CONTROL_TYPES]
    retrieval_hits = sum(result.retrieval_hit for result in mutation_results)
    llm_successes = sum(
        result.retrieval_hit
        and set(result.expected_review_targets).issubset(
            {
                item.source_id
                for item in result.final_reviews
                if item.status is FinalStatus.VERIFIED_REVIEW
            }
        )
        for result in mutation_results
    )
    false_alarms = sum(
        any(item.status is FinalStatus.VERIFIED_REVIEW for item in result.final_reviews)
        for result in control_results
    )
    blocked = sum(
        item.status is FinalStatus.REJECTED_UNSUPPORTED
        for result in results
        for item in result.final_reviews
    )
    overall_candidates = sum(len(result.candidates) for result in results)
    overall_verified = sum(
        item.status is FinalStatus.VERIFIED_REVIEW
        for result in results
        for item in result.final_reviews
    )
    overall_proposed = sum(
        proposal.decision.value == "REVIEW"
        for result in results
        for proposal in result.proposed_reviews
    )
    overall_target_retained = sum(
        set(result.expected_review_targets).issubset(
            {
                item.source_id
                for item in result.final_reviews
                if item.status is FinalStatus.VERIFIED_REVIEW
            }
        )
        for result in mutation_results
    )
    overall_evidence_complete = sum(
        bool(item.evidence and item.short_reason)
        for result in results
        for item in result.final_reviews
        if item.status is FinalStatus.VERIFIED_REVIEW
    )
    overall_unsupported: int | dict[str, int] = blocked
    if complete_overall:
        overall_unsupported = {
            "proposed_reviews": overall_proposed,
            "blocked": blocked,
            "final_verified_reviews": overall_verified,
        }
    return {
        "definitions": {
            "retrieval_coverage": "Complete frozen expected target set present in Top-K.",
            "llm_review_success": "Complete frozen expected target set retained as VERIFIED_REVIEW among retrieval-hit mutations.",
            "false_alarm": "Control case with at least one final VERIFIED_REVIEW.",
            "review_selection_added_value": "Reduction from identical fixed candidates to evidence-backed verified reviews while tracking frozen-target retention.",
            "unsupported_output_blocked": "REVIEW proposal rejected before final exposure by deterministic or independent verification.",
        },
        "overall": {
            "cases": len(results),
            "mutation_cases": len(mutation_results),
            "control_cases": len(control_results),
            "retrieval_coverage": {
                "hits": retrieval_hits,
                "eligible": len(mutation_results),
                "rate": _safe_rate(retrieval_hits, len(mutation_results)),
            },
            "llm_review_success": {
                "successes": llm_successes,
                "eligible_retrieval_hits": retrieval_hits,
                "rate": _safe_rate(llm_successes, retrieval_hits),
            },
            "false_alarm": {
                "cases": false_alarms,
                "eligible_controls": len(control_results),
                "rate": _safe_rate(false_alarms, len(control_results)),
            },
            **(
                {
                    "review_selection_added_value": {
                        "baseline_candidates": overall_candidates,
                        "final_verified_reviews": overall_verified,
                        "candidate_reduction_ratio": _safe_rate(
                            overall_candidates - overall_verified,
                            overall_candidates,
                        ),
                        "expected_target_retained_cases": overall_target_retained,
                        "verified_reviews_with_evidence_and_reason": overall_evidence_complete,
                    }
                }
                if complete_overall
                else {}
            ),
            "unsupported_output_blocked": overall_unsupported,
        },
        "by_type": by_type,
    }
