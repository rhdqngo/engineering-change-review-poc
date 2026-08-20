import json

import pytest

from ecr_poc.data import active_data_root, repository_root
from ecr_poc.metrics import calculate_metrics
from ecr_poc.models import PipelineResult
from ecr_poc.storage import (
    _frozen_paths,
    _validated_run,
    v6_freeze_payload_relatives,
)


def test_v5_freeze_upload_includes_embedding_reproducibility_manifest() -> None:
    paths = {
        path.relative_to(repository_root()).as_posix()
        for path in _frozen_paths(repository_root())
    }
    assert "data/embeddings/ecr-poc-v5.json" in paths


def test_v6_pre_freeze_payload_set_is_exact_and_excludes_mutable_manifest() -> None:
    root = active_data_root()
    assert v6_freeze_payload_relatives(root) == (
        "data/embeddings/ecr-poc-v6-vectors.f32",
        "data/embeddings/ecr-poc-v6.json",
        "data/nasa/cfs-v7.0.1-artifacts.jsonl.gz",
        "data/nasa/cfs-v7.0.1-raw-sources.tar.gz",
        "data/relations/ecr-poc-v6-identifiers.json.gz",
    )


def test_retained_v1_run_passes_publish_integrity_checks() -> None:
    content = (repository_root() / "results" / "runs" / "vertex-adk.json").read_bytes()
    run = _validated_run(content)
    assert len(run.cases) == 18
    assert run.metrics["overall"]["retrieval_coverage"]["hits"] == 10


def test_v6_fixture_result_has_complete_top_10_and_sanitized_role_traces() -> None:
    content = (
        repository_root() / "results" / "runs" / "fixture-v6-baseline.json"
    ).read_bytes()
    run = _validated_run(content)
    assert len(run.cases) == 20
    assert all(len(case.candidates) == 10 for case in run.cases)
    assert all(
        not trace.raw_output for case in run.cases for trace in case.role_traces
    )


def test_publish_integrity_rejects_changed_candidate_arm() -> None:
    path = repository_root() / "results" / "runs" / "vertex-adk.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cases"][0]["proposed_candidate_source_ids"] = []
    with pytest.raises(RuntimeError, match="Baseline/Proposed arms differ"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_publish_integrity_rejects_role_errors() -> None:
    path = repository_root() / "results" / "runs" / "vertex-adk.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cases"][0]["role_traces"][0]["error"] = "simulated"
    with pytest.raises(RuntimeError, match="contains a role error"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_publish_integrity_rejects_duplicate_verified_reviews() -> None:
    path = repository_root() / "results" / "runs" / "fixture-v5-baseline.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    verified = next(
        review
        for review in payload["cases"][0]["final_reviews"]
        if review["status"] == "VERIFIED_REVIEW"
    )
    payload["cases"][0]["final_reviews"].append(dict(verified))
    payload["metrics"] = calculate_metrics(
        [PipelineResult.model_validate(case) for case in payload["cases"]],
        complete_overall=True,
    )
    with pytest.raises(RuntimeError, match="duplicate verified reviews"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_v5_integrity_rejects_embedding_index_fingerprint_drift() -> None:
    payload = json.loads(
        (repository_root() / "results/runs/vertex-adk-v5.json").read_text(
            encoding="utf-8"
        )
    )
    payload["cases"][0]["embedding_index_fingerprint"] = "0" * 64
    with pytest.raises(RuntimeError, match="embedding index fingerprint mismatch"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_v6_integrity_rejects_exposed_unverified_claim() -> None:
    path = repository_root() / "results/runs/fixture-v6-baseline.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidate_result = next(
        item
        for item in payload["cases"][0]["candidate_results"]
        if item["status"] != "VERIFIED_REVIEW"
    )
    verified = next(
        item
        for item in payload["cases"][0]["candidate_results"]
        if item["status"] == "VERIFIED_REVIEW"
    )
    candidate_result["verified_claims"] = [
        dict(verified["verified_claims"][0])
    ]
    payload["metrics"] = calculate_metrics(
        [PipelineResult.model_validate(case) for case in payload["cases"]]
    )
    with pytest.raises(RuntimeError, match="unsupported claim was exposed"):
        _validated_run(json.dumps(payload).encode("utf-8"))
