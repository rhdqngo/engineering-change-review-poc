from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from .data import load_cases, repository_root
from .models import EvaluationRun, FinalStatus


def _verified_sources(case: Any) -> set[str]:
    return {
        review.source_id
        for review in case.final_reviews
        if review.status is FinalStatus.VERIFIED_REVIEW
    }


def _verifier_supported(case: Any, source_id: str, evidence: str) -> bool:
    for trace in case.role_traces:
        if trace.role != "evidence_verifier" or not isinstance(trace.parsed, dict):
            continue
        verifications = trace.parsed.get("verifications")
        if not isinstance(verifications, list):
            continue
        for item in verifications:
            if not isinstance(item, dict):
                continue
            supported = item.get("supported") is True or item.get("verdict") == "SUPPORTED"
            verifier_evidence = item.get("evidence")
            evidence_matches = verifier_evidence is None or verifier_evidence == evidence
            if item.get("source_id") == source_id and evidence_matches and supported:
                return True
    return False


def classify_case(case_definition: Any, result: Any) -> dict[str, Any]:
    expected = set(case_definition.expected_review_targets)
    candidates = {candidate.source_id: candidate for candidate in result.candidates}
    verified = _verified_sources(result)
    verifier_pass_errors: list[str] = []
    for review in result.final_reviews:
        if review.status is not FinalStatus.VERIFIED_REVIEW:
            continue
        candidate = candidates.get(review.source_id)
        if (
            candidate is None
            or not review.evidence
            or review.evidence not in candidate.content
            or not _verifier_supported(result, review.source_id, review.evidence)
        ):
            verifier_pass_errors.append(review.source_id)
    mutation = bool(expected)
    return {
        "retrieval_miss": sorted(expected - set(candidates)),
        "expected_target_miss": sorted(expected - verified),
        "mutation_unnecessary_warnings": sorted(verified - expected) if mutation else [],
        "control_false_alarm": sorted(verified) if not mutation else [],
        "verifier_pass_error": sorted(verifier_pass_errors),
    }


def _target_ranks(case_definition: Any, result: Any) -> dict[str, int | None]:
    ranks = {candidate.source_id: candidate.rank for candidate in result.candidates}
    return {
        source_id: ranks.get(source_id)
        for source_id in case_definition.expected_review_targets
    }


def _rank_summary(values: list[int | None]) -> dict[str, float | int]:
    present = [value for value in values if value is not None]
    return {
        "targets": len(values),
        "retrieved": len(present),
        "mean_rank": round(statistics.mean(present), 6) if present else 0.0,
        "mean_reciprocal_rank": (
            round(statistics.mean(1 / value for value in present), 6) if present else 0.0
        ),
    }


def compare_runs(
    baseline_path: Path,
    variant_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root = root or repository_root()
    baseline = EvaluationRun.model_validate_json(baseline_path.read_bytes())
    variant = EvaluationRun.model_validate_json(variant_path.read_bytes())
    baseline_manifest = (
        baseline.provenance.experiment_manifest if baseline.provenance else None
    )
    variant_manifest = variant.provenance.experiment_manifest if variant.provenance else None
    _, _, definitions = load_cases(root, baseline_manifest)
    _, _, variant_definitions = load_cases(root, variant_manifest)
    baseline_by_id = {case.case_id: case for case in baseline.cases}
    variant_by_id = {case.case_id: case for case in variant.cases}
    expected_ids = {case.id for case in definitions}
    if {case.id for case in variant_definitions} != expected_ids:
        raise ValueError("Quality manifests do not use the same frozen case set")
    if set(baseline_by_id) != expected_ids or set(variant_by_id) != expected_ids:
        raise ValueError(
            "Both quality runs must contain the complete frozen case set"
        )
    baseline_query = baseline.configuration.get("query_version", "structured-change-v1")
    variant_query = variant.configuration.get("query_version", "structured-change-v1")
    invariant_checks = {
        "provider": baseline.provider == variant.provider,
        "model": baseline.model == variant.model,
        "embedding_model": baseline.embedding_model == variant.embedding_model,
        "embedding_index_fingerprint": (
            baseline.configuration.get("embedding_index_fingerprint")
            == variant.configuration.get("embedding_index_fingerprint")
        ),
        "top_k": baseline.configuration.get("top_k") == variant.configuration.get("top_k"),
        "fusion": baseline.configuration.get("fusion") == variant.configuration.get("fusion"),
        "prompt_hashes": (
            baseline.provenance is not None
            and variant.provenance is not None
            and baseline.provenance.prompt_hashes == variant.provenance.prompt_hashes
        ),
        "query_version_changed": baseline_query != variant_query,
    }
    if not all(invariant_checks.values()):
        failed = [name for name, passed in invariant_checks.items() if not passed]
        raise ValueError(f"Quality comparison invariant failed: {', '.join(failed)}")
    case_rows: list[dict[str, Any]] = []
    baseline_ranks: list[int | None] = []
    variant_ranks: list[int | None] = []
    changed_candidate_sequences = 0
    for definition in definitions:
        baseline_case = baseline_by_id[definition.id]
        variant_case = variant_by_id[definition.id]
        before_ranks = _target_ranks(definition, baseline_case)
        after_ranks = _target_ranks(definition, variant_case)
        baseline_ranks.extend(before_ranks.values())
        variant_ranks.extend(after_ranks.values())
        if baseline_case.candidate_fingerprint != variant_case.candidate_fingerprint:
            changed_candidate_sequences += 1
        rank_changes = {
            source_id: {
                "baseline": before_ranks[source_id],
                "variant": after_ranks[source_id],
            }
            for source_id in before_ranks
        }
        case_rows.append(
            {
                "case_id": definition.id,
                "type": definition.type,
                "baseline_failures": classify_case(definition, baseline_case),
                "variant_failures": classify_case(definition, variant_case),
                "expected_target_ranks": rank_changes,
            }
        )
    before = _rank_summary(baseline_ranks)
    after = _rank_summary(variant_ranks)
    return {
        "baseline": {
            "run_id": baseline.run_id,
            "experiment_id": baseline.experiment_id,
            "query_version": baseline_query,
            "target_rank_summary": before,
        },
        "variant": {
            "run_id": variant.run_id,
            "experiment_id": variant.experiment_id,
            "query_version": variant_query,
            "target_rank_summary": after,
        },
        "invariant_checks": invariant_checks,
        "candidate_sequences_changed": changed_candidate_sequences,
        "delta": {
            "mean_rank": round(after["mean_rank"] - before["mean_rank"], 6),
            "mean_reciprocal_rank": round(
                after["mean_reciprocal_rank"] - before["mean_reciprocal_rank"], 6
            ),
        },
        "cases": case_rows,
    }


def write_comparison(
    baseline_path: Path,
    variant_path: Path,
    output_path: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    comparison = compare_runs(baseline_path, variant_path, root=root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return comparison
