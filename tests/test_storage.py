import asyncio
import json
from pathlib import Path

import pytest

from ecr_poc.data import repository_root
from ecr_poc.evaluation import evaluate
from ecr_poc.metrics import calculate_metrics
from ecr_poc.models import PipelineResult
from ecr_poc.storage import _frozen_paths, _validated_run


def test_v5_freeze_upload_includes_embedding_reproducibility_manifest() -> None:
    paths = {
        path.relative_to(repository_root()).as_posix()
        for path in _frozen_paths(repository_root())
    }
    assert "data/embeddings/ecr-poc-v5.json" in paths


def test_retained_v1_run_passes_publish_integrity_checks() -> None:
    content = (repository_root() / "results" / "runs" / "vertex-adk.json").read_bytes()
    run = _validated_run(content)
    assert len(run.cases) == 18
    assert run.metrics["overall"]["retrieval_coverage"]["hits"] == 10


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


def test_cloud_v2_integrity_requires_one_supported_verifier_verdict() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-v2-publication.json"),
            experiment_manifest="ecr-poc-v2.json",
            run_id="strict-v2-run",
            source_commit="0123456789abcdef",
            update_latest=False,
        )
    )
    payload = run.model_dump(mode="json")
    payload["provider"] = "vertex-adk"
    payload["model"] = "gemini-3.5-flash"
    payload["embedding_model"] = "gemini-embedding-001"
    payload["provenance"].update(
        {
            "artifact_store": "gcs",
            "cloud_execution": "ecr-poc-evaluate-abcde",
            "container_image_digest": "asia-docker.pkg.dev/p/r/i@sha256:" + "a" * 64,
        }
    )
    for case in payload["cases"]:
        case["provider"] = "vertex-adk"
        case["model"] = "gemini-3.5-flash"
        case["embedding_model"] = "gemini-embedding-001"
        for trace in case["role_traces"]:
            trace["provider"] = "vertex-adk"
            trace["model"] = "gemini-3.5-flash"

    content = json.dumps(payload).encode("utf-8")
    payload["provenance"].pop("experiment_manifest")
    content = json.dumps(payload).encode("utf-8")
    assert (
        _validated_run(
            content,
            require_cloud=True,
            expected_experiment_manifest="ecr-poc-v2.json",
        ).run_id
        == "strict-v2-run"
    )

    first_case = payload["cases"][0]
    verifier = next(
        trace
        for trace in first_case["role_traces"]
        if trace["role"] == "evidence_verifier"
    )
    verifier["parsed"]["verifications"].append(
        verifier["parsed"]["verifications"][0]
    )
    with pytest.raises(RuntimeError, match="one supported verifier verdict"):
        _validated_run(
            json.dumps(payload).encode("utf-8"),
            require_cloud=True,
            expected_experiment_manifest="ecr-poc-v2.json",
        )


def test_cloud_v3_integrity_requires_explicit_manifest() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-v3-publication.json"),
            experiment_manifest="ecr-poc-v3.json",
            run_id="strict-v3-run",
            source_commit="0123456789abcdef",
            update_latest=False,
        )
    )
    payload = run.model_dump(mode="json")
    payload["provenance"]["experiment_manifest"] = None
    with pytest.raises(ValueError, match="require an experiment manifest"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_cloud_v4_integrity_requires_explicit_manifest() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-v4-publication.json"),
            experiment_manifest="ecr-poc-v4.json",
            run_id="strict-v4-run",
            source_commit="0123456789abcdef",
            update_latest=False,
        )
    )
    payload = run.model_dump(mode="json")
    payload["provenance"]["experiment_manifest"] = None
    with pytest.raises(ValueError, match="require an experiment manifest"):
        _validated_run(json.dumps(payload).encode("utf-8"))


def test_v5_integrity_rejects_embedding_index_fingerprint_drift() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-v5-fingerprint.json"),
            experiment_manifest="ecr-poc-v5.json",
            run_id="strict-v5-run",
            source_commit="WORKTREE-V5-TEST",
            update_latest=False,
        )
    )
    payload = run.model_dump(mode="json")
    payload["cases"][0]["embedding_index_fingerprint"] = "0" * 64
    with pytest.raises(RuntimeError, match="embedding index fingerprint mismatch"):
        _validated_run(json.dumps(payload).encode("utf-8"))
