import json
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from ecr_poc.data import (
    DataIntegrityError,
    active_data_root,
    load_artifacts,
    load_cases,
    repository_root,
    validate_all,
    validate_experiment_manifest,
)
from ecr_poc.embedding_index import (
    MAX_EMBEDDING_INPUT_UTF8_BYTES,
    load_embedding_index,
)
from ecr_poc.identifier_index import load_identifier_index, write_identifier_index
from ecr_poc.query_processing import process_query
from ecr_poc.retrieval import DeterministicHashEmbedder, HybridRetriever, VertexEmbedder


def test_frozen_data_integrity_and_distribution() -> None:
    assert validate_all() == {
        "artifacts": 35515,
        "cases": 20,
        "direct": 5,
        "semantic": 5,
        "cross_artifact": 5,
        "clean": 2,
        "benign": 3,
    }


def _v6_retriever() -> HybridRetriever:
    root = active_data_root()
    artifacts = load_artifacts()
    index = load_embedding_index(root, "data/embeddings/ecr-poc-v6.json", artifacts)
    manifest = json.loads(
        (root / "data/experiments/ecr-poc-v6.json").read_text(encoding="utf-8")
    )
    return HybridRetriever(
        artifacts,
        DeterministicHashEmbedder(index.dimensions),
        document_embeddings=index.vectors,
        embedding_index_fingerprint=index.fingerprint,
        identifier_index=load_identifier_index(
            root / manifest["identifier_index_file"],
            artifacts,
            expected_artifact_package_sha256=manifest["files"][
                manifest["artifact_package_file"]
            ],
            expected_sha256=manifest["files"][manifest["identifier_index_file"]],
        ),
    )


def test_incoming_artifact_is_query_only_and_top_k_is_fixed() -> None:
    _, top_k, cases = load_cases()
    retriever = _v6_retriever()
    corpus_ids = {artifact.source_id for artifact in retriever.artifacts}
    for case in cases:
        assert case.incoming_artifact is not None
        retrieval = retriever.retrieve(case.incoming_artifact, final_k=top_k)
        assert len(retrieval.broad_candidates) == 40
        assert len(retrieval.expanded_candidates) <= 200
        assert len(retrieval.final_docket) == 10
        assert all(candidate.source_id in corpus_ids for candidate in retrieval.final_docket)
        assert case.incoming_artifact.text not in corpus_ids
        assert "query_text" not in retrieval.query_processing.model_dump()


def test_v6_artifacts_fit_the_provider_preflight_byte_envelope() -> None:
    assert all(
        len(f"{artifact.title}\n{artifact.content}".encode())
        <= MAX_EMBEDDING_INPUT_UTF8_BYTES
        for artifact in load_artifacts()
    )


def test_retrieval_is_deterministic() -> None:
    _, top_k, cases = load_cases()
    retriever = _v6_retriever()
    assert cases[0].incoming_artifact is not None
    first = retriever.retrieve(cases[0].incoming_artifact, final_k=top_k)
    second = retriever.retrieve(cases[0].incoming_artifact, final_k=top_k)
    assert first.model_dump() == second.model_dump()
    assert first.summary.broad_candidate_fingerprint
    assert first.summary.expanded_pool_fingerprint
    assert first.summary.final_docket_fingerprint


def test_query_processor_is_deterministic_and_does_not_invent_old_values() -> None:
    _, _, cases = load_cases()
    incoming = cases[0].incoming_artifact
    assert incoming is not None
    first = process_query(incoming)
    second = process_query(incoming)
    assert first == second
    assert first.processor_version == "incoming-query-v2-deterministic"
    assert "old_value" not in first.query_text
    assert "dependency" not in first.query_text


def test_identifier_index_generation_is_byte_identical() -> None:
    root = active_data_root()
    artifacts = load_artifacts()
    manifest = json.loads(
        (root / "data/experiments/ecr-poc-v6.json").read_text(encoding="utf-8")
    )
    test_root = repository_root() / ".runtime" / f"identifier-index-{uuid.uuid4()}"
    first = test_root / "first.json.gz"
    second = test_root / "second.json.gz"
    a = write_identifier_index(
        first, artifacts, manifest["files"][manifest["artifact_package_file"]]
    )
    b = write_identifier_index(
        second, artifacts, manifest["files"][manifest["artifact_package_file"]]
    )
    assert first.read_bytes() == second.read_bytes()
    assert a["sha256"] == b["sha256"]
    assert a["fingerprint"] == b["fingerprint"]


def test_vertex_document_cache_checkpoints_batches_but_never_queries() -> None:
    calls: list[tuple[str, ...]] = []
    cache_root = repository_root() / ".runtime" / f"test-embedding-cache-{uuid.uuid4()}"

    class FakeModels:
        def embed_content(self, **kwargs):
            contents = tuple(kwargs["contents"])
            calls.append(contents)
            return SimpleNamespace(
                embeddings=[SimpleNamespace(values=[1.0, 0.0]) for _ in contents]
            )

    def make_embedder() -> VertexEmbedder:
        embedder = object.__new__(VertexEmbedder)
        embedder.model_name = "gemini-embedding-001"
        embedder.output_dimensionality = 2
        embedder.client = SimpleNamespace(models=FakeModels())
        embedder.cache_path = cache_root / "vertex-embeddings.json"
        embedder._cache = embedder._read_cache()
        return embedder

    documents = [f"document-{index}" for index in range(101)]
    first = make_embedder()
    assert len(first.embed_documents(documents)) == 101
    assert len(calls) == 2
    assert len(list(first.cache_path.with_suffix(".parts").glob("*.json"))) == 2

    second = make_embedder()
    assert len(second.embed_documents(documents)) == 101
    assert len(calls) == 2
    assert second.embed_documents(["duplicate", "duplicate"]) == [
        [1.0, 0.0],
        [1.0, 0.0],
    ]
    assert len(calls) == 3
    assert second.embed_query("private incoming artifact") == [1.0, 0.0]
    assert len(calls) == 4
    assert len(list(second.cache_path.with_suffix(".parts").glob("*.json"))) == 3


def test_v6_case_contract_and_target_specific_evidence() -> None:
    _, _, cases = load_cases()
    assert all(case.incoming_artifact for case in cases)
    assert all(case.basis_source_ids for case in cases)
    assert all(
        {item.source_id for item in case.expected_evidence_by_target}
        == set(case.expected_review_targets)
        for case in cases
    )
    assert all(
        {slot.source_id for slot in case.expected_claims}
        == set(case.expected_review_targets)
        for case in cases
    )


def _copy_active_freeze(test_root: Path) -> None:
    active = active_data_root()
    shutil.copytree(active / "data", test_root / "data", dirs_exist_ok=True)
    requirements = Path(
        "docs/plans/LLM 기반 우주 Engineering Change Review.md"
    )
    destination = test_root / requirements
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(active / requirements, destination)


def test_v6_prompt_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / f"test-data-drift-{uuid.uuid4()}"
    _copy_active_freeze(test_root)
    prompt_path = test_root / "data" / "prompts" / "ecr-poc-v6.json"
    prompt_path.write_text(prompt_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v6 frozen file hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v6_role_prompt_hash_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / f"test-role-drift-{uuid.uuid4()}"
    _copy_active_freeze(test_root)
    manifest_path = test_root / "data" / "experiments" / "ecr-poc-v6.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["prompt_hashes"]["engineering_review"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="v6 role prompt hash mismatch"):
        validate_experiment_manifest(test_root)


def test_v6_design_provenance_drift_breaks_the_experiment_freeze() -> None:
    test_root = repository_root() / ".runtime" / f"test-design-drift-{uuid.uuid4()}"
    _copy_active_freeze(test_root)
    manifest_path = test_root / "data" / "experiments" / "ecr-poc-v6.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["requirements"]["design_commit"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="design-freeze commit changed"):
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
