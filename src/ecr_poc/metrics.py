from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from .models import FinalStatus, PipelineResult

MUTATION_TYPES = {"direct", "semantic", "cross_artifact"}
CONTROL_TYPES = {"clean", "benign"}


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def calculate_metrics(
    results: Sequence[PipelineResult], *, complete_overall: bool = False
) -> dict[str, Any]:
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
