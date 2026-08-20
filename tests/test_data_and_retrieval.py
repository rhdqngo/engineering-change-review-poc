import json
import shutil
import uuid

import pytest

from ecr_poc.data import (
    DataIntegrityError,
    load_artifacts,
    load_cases,
    repository_root,
    validate_all,
    validate_experiment_manifest,
)
from ecr_poc.retrieval import DeterministicHashEmbedder, HybridRetriever


def test_frozen_data_integrity_and_distribution() -> None:
    assert validate_all() == {
        "artifacts": 32,
        "cases": 18,
        "direct": 4,
        "semantic": 4,
        "cross_artifact": 4,
        "clean": 3,
        "benign": 3,
    }


def test_offline_retrieval_covers_every_frozen_mutation_target() -> None:
    _, top_k, cases = load_cases()
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    for case in cases:
        candidates = retriever.retrieve(case.change, top_k)
        candidate_ids = {candidate.source_id for candidate in candidates}
        if case.expected_review_targets:
            assert set(case.expected_review_targets).issubset(candidate_ids), case.id


def test_retrieval_is_deterministic() -> None:
    _, top_k, cases = load_cases()
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    first = retriever.retrieve(cases[0].change, top_k)
    second = retriever.retrieve(cases[0].change, top_k)
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]


def test_v5_case_contract_and_target_specific_evidence() -> None:
    _, _, cases = load_cases()
    assert all(case.changed_source_id for case in cases)
    assert all(case.original_content and case.changed_content for case in cases)
    assert all(
        {item.source_id for item in case.expected_evidence_by_target}
        == set(case.expected_review_targets)
        for case in cases
    )


def test_v5_prompt_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / f"test-data-drift-{uuid.uuid4()}"
    shutil.copytree(repository_root() / "data", test_root / "data", dirs_exist_ok=True)
    prompt_path = test_root / "data" / "prompts" / "ecr-poc-v2.json"
    prompt_path.write_text(prompt_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v5 frozen file hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v5_role_prompt_hash_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / f"test-role-drift-{uuid.uuid4()}"
    shutil.copytree(repository_root() / "data", test_root / "data", dirs_exist_ok=True)
    manifest_path = test_root / "data" / "experiments" / "ecr-poc-v5.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["prompt_hashes"]["engineering_review"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v5 role prompt hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v4_manifest_remains_valid_for_historical_results() -> None:
    validated = validate_experiment_manifest(name="ecr-poc-v4.json")
    assert "data/prompts/ecr-poc-v2.json" in validated


def test_v5_q1_manifest_changes_only_the_frozen_query_contract() -> None:
    baseline = json.loads(
        (repository_root() / "data/experiments/ecr-poc-v5.json").read_text(
            encoding="utf-8"
        )
    )
    variant = json.loads(
        (repository_root() / "data/experiments/ecr-poc-v5-q1.json").read_text(
            encoding="utf-8"
        )
    )
    validate_experiment_manifest(name="ecr-poc-v5-q1.json")
    assert baseline["retrieval"]["query_version"] == "structured-change-v1"
    assert variant["retrieval"]["query_version"] == (
        "structured-change-v2-artifact-delta"
    )
    assert baseline["files"] == variant["files"]
    assert baseline["prompt_hashes"] == variant["prompt_hashes"]
    assert baseline["retrieval"]["fusion"] == variant["retrieval"]["fusion"]
    assert baseline["embedding_index_file"] == variant["embedding_index_file"]


def test_v2_manifest_remains_valid_for_historical_results() -> None:
    validated = validate_experiment_manifest(name="ecr-poc-v2.json")
    assert "data/cases/freeze.json" in validated


def test_v3_manifest_remains_valid_for_historical_results() -> None:
    validated = validate_experiment_manifest(name="ecr-poc-v3.json")
    assert "data/prompts/ecr-poc-v2.json" in validated
