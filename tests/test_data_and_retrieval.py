import json
import shutil

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


def test_v4_prompt_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / "test-data-drift"
    shutil.copytree(repository_root() / "data", test_root / "data", dirs_exist_ok=True)
    prompt_path = test_root / "data" / "prompts" / "ecr-poc-v2.json"
    prompt_path.write_text(prompt_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v4 frozen file hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v4_role_prompt_hash_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / "test-role-prompt-drift"
    shutil.copytree(repository_root() / "data", test_root / "data", dirs_exist_ok=True)
    manifest_path = test_root / "data" / "experiments" / "ecr-poc-v4.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["prompt_hashes"]["engineering_review"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v4 role prompt hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v2_manifest_remains_valid_for_historical_results() -> None:
    validated = validate_experiment_manifest(name="ecr-poc-v2.json")
    assert "data/cases/freeze.json" in validated


def test_v3_manifest_remains_valid_for_historical_results() -> None:
    validated = validate_experiment_manifest(name="ecr-poc-v3.json")
    assert "data/prompts/ecr-poc-v2.json" in validated
