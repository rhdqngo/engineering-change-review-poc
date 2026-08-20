from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from .data import (
    active_data_root,
    experiment_manifest_name,
    is_v6_experiment_id,
    load_experiment_manifest,
    repository_root,
    sha256_file,
    validate_experiment_manifest,
)
from .metrics import calculate_metrics
from .models import (
    CandidateFinalStatus,
    EvaluationRun,
    FinalStatus,
    PublishedPointer,
    VerifierVerdict,
)
from .observability import log_event
from .retrieval import candidate_fingerprint


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class StoredObject:
    uri: str
    generation: int | None
    sha256: str


class RunStore(Protocol):
    kind: str
    location: str

    def write_checkpoint(self, payload: dict[str, Any]) -> StoredObject: ...

    def write_failure(self, payload: dict[str, Any]) -> StoredObject: ...

    def write_final(self, run: EvaluationRun) -> StoredObject: ...


class LocalRunStore:
    kind = "local"

    def __init__(
        self,
        output_path: Path,
        *,
        update_latest: bool = True,
        latest_path: Path | None = None,
    ) -> None:
        self.output_path = output_path
        self.checkpoint_path = output_path.with_suffix(".checkpoint.json")
        self.failure_path = output_path.with_suffix(".failure.json")
        self.update_latest = update_latest
        self.latest_path = latest_path
        self.location = str(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, path: Path, value: Any) -> StoredObject:
        content = json_bytes(value)
        path.write_bytes(content)
        return StoredObject(
            uri=str(path),
            generation=None,
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def write_checkpoint(self, payload: dict[str, Any]) -> StoredObject:
        return self._write(self.checkpoint_path, payload)

    def write_failure(self, payload: dict[str, Any]) -> StoredObject:
        return self._write(self.failure_path, payload)

    def write_final(self, run: EvaluationRun) -> StoredObject:
        stored = self._write(self.output_path, run.model_dump(mode="json"))
        if self.update_latest:
            latest = self.latest_path or self.output_path.parent / "latest.json"
            self._write(latest, run.model_dump(mode="json"))
        return stored


def _storage_client() -> Any:
    from google.cloud import storage  # type: ignore[attr-defined,import-untyped]

    return storage.Client()


class GcsRunStore:
    kind = "gcs"

    def __init__(self, bucket_name: str, run_id: str, prefix: str = "runs") -> None:
        self.bucket_name = bucket_name
        self.run_id = run_id
        self.prefix = prefix.strip("/")
        self.client = _storage_client()
        self.bucket = self.client.bucket(bucket_name)
        self.location = f"gs://{bucket_name}/{self.prefix}/{run_id}/evaluation.json"
        self._checkpoint_generation: int | None = None

    def _name(self, leaf: str) -> str:
        return f"{self.prefix}/{self.run_id}/{leaf}"

    def _upload(
        self,
        name: str,
        value: Any,
        *,
        immutable: bool,
        generation: int | None = None,
    ) -> StoredObject:
        content = json_bytes(value)
        blob = self.bucket.blob(name)
        precondition = 0 if immutable or generation is None else generation
        blob.upload_from_string(
            content,
            content_type="application/json",
            if_generation_match=precondition,
        )
        return StoredObject(
            uri=f"gs://{self.bucket_name}/{name}",
            generation=int(blob.generation) if blob.generation is not None else None,
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def write_checkpoint(self, payload: dict[str, Any]) -> StoredObject:
        stored = self._upload(
            self._name("checkpoint.json"),
            payload,
            immutable=False,
            generation=self._checkpoint_generation,
        )
        self._checkpoint_generation = stored.generation
        return stored

    def write_failure(self, payload: dict[str, Any]) -> StoredObject:
        return self._upload(self._name("failure.json"), payload, immutable=True)

    def write_final(self, run: EvaluationRun) -> StoredObject:
        return self._upload(
            self._name("evaluation.json"),
            run.model_dump(mode="json"),
            immutable=True,
        )


def _frozen_paths(root: Path) -> Iterable[Path]:
    for relative in [
        "data/cases",
        "data/embeddings",
        "data/nasa",
        "data/experiments",
        "data/prompts",
        "data/relations",
    ]:
        base = root / relative
        yield from (path for path in base.rglob("*") if path.is_file())
    requirements = root / "docs" / "plans" / "LLM 기반 우주 Engineering Change Review.md"
    if requirements.is_file():
        yield requirements


def v6_freeze_payload_relatives(
    root: Path, manifest_name: str = "ecr-poc-v6.json"
) -> tuple[str, ...]:
    manifest = load_experiment_manifest(root, manifest_name)
    index_file = str(manifest["embedding_index_file"])
    index = json.loads((root / index_file).read_text(encoding="utf-8"))
    return tuple(
        sorted(
            {
                str(manifest["artifact_package_file"]),
                str(manifest["raw_source_archive_file"]),
                index_file,
                str(index["vector_file"]),
                str(manifest["identifier_index_file"]),
            }
        )
    )


def upload_frozen_tree(
    root: Path,
    bucket_name: str,
    prefix: str,
    *,
    only_relatives: Iterable[str] | None = None,
) -> dict[str, Any]:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    uploaded = 0
    existing = 0
    objects: dict[str, dict[str, int | str]] = {}
    if only_relatives is None:
        paths = sorted(_frozen_paths(root))
    else:
        paths = [root / relative for relative in sorted(set(only_relatives))]
        missing = [path for path in paths if not path.is_file()]
        if missing:
            raise RuntimeError(f"Frozen upload input is missing: {missing[0]}")
    for path in paths:
        relative = path.relative_to(root).as_posix()
        name = f"{prefix.strip('/')}/{relative}"
        content = path.read_bytes()
        blob = bucket.blob(name)
        try:
            blob.upload_from_string(content, if_generation_match=0)
            uploaded += 1
        except Exception as error:
            if type(error).__name__ not in {"PreconditionFailed", "Conflict"}:
                raise
            remote = blob.download_as_bytes()
            if hashlib.sha256(remote).digest() != hashlib.sha256(content).digest():
                raise RuntimeError(f"Frozen GCS object differs: gs://{bucket_name}/{name}") from error
            existing += 1
        blob.reload()
        objects[relative] = {
            "generation": int(blob.generation),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    return {
        "uploaded": uploaded,
        "verified_existing": existing,
        "objects": objects,
    }


def upload_historical_result(root: Path, bucket_name: str) -> StoredObject:
    path = root / "results" / "runs" / "vertex-adk.json"
    content = path.read_bytes()
    name = "historical/v1/vertex-adk.json"
    client = _storage_client()
    blob = client.bucket(bucket_name).blob(name)
    try:
        blob.upload_from_string(
            content,
            content_type="application/json",
            if_generation_match=0,
        )
    except Exception as error:
        if type(error).__name__ not in {"PreconditionFailed", "Conflict"}:
            raise
        remote = blob.download_as_bytes()
        if hashlib.sha256(remote).digest() != hashlib.sha256(content).digest():
            raise RuntimeError("Historical v1 GCS object differs") from error
    blob.reload()
    return StoredObject(
        uri=f"gs://{bucket_name}/{name}",
        generation=int(blob.generation),
        sha256=hashlib.sha256(content).hexdigest(),
    )


def seed_historical_pointer(
    root: Path, bucket_name: str, source_commit: str
) -> PublishedPointer:
    stored = upload_historical_result(root, bucket_name)
    if stored.generation is None:
        raise RuntimeError("Historical result has no GCS generation")
    content = (root / "results" / "runs" / "vertex-adk.json").read_bytes()
    run = _validated_run(content)
    pointer = PublishedPointer(
        run_id=run.run_id,
        experiment_id=run.experiment_id,
        object_name="historical/v1/vertex-adk.json",
        generation=stored.generation,
        sha256=stored.sha256,
        published_at=datetime.now(UTC).isoformat(),
        source_commit=source_commit,
    )
    client = _storage_client()
    blob = client.bucket(bucket_name).blob("published/demo.json")
    if blob.exists():
        return PublishedPointer.model_validate_json(blob.download_as_bytes())
    blob.upload_from_string(
        json_bytes(pointer.model_dump(mode="json")),
        content_type="application/json",
        if_generation_match=0,
    )
    return pointer


def materialize_gcs_prefix(
    bucket_name: str, prefix: str, target_root: Path
) -> dict[str, int]:
    client = _storage_client()
    normalized = prefix.strip("/") + "/"
    count = 0
    total_bytes = 0
    for blob in client.list_blobs(bucket_name, prefix=normalized):
        relative = blob.name[len(normalized) :]
        if not relative or relative.endswith("/"):
            continue
        destination = (target_root / relative).resolve()
        if target_root.resolve() not in destination.parents:
            raise RuntimeError(f"Unsafe GCS object path: {blob.name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = blob.download_as_bytes()
        destination.write_bytes(content)
        count += 1
        total_bytes += len(content)
    if count == 0:
        raise RuntimeError(f"No frozen inputs found at gs://{bucket_name}/{normalized}")
    return {"objects": count, "bytes": total_bytes}


def _validate_cloud_provenance(
    run: EvaluationRun,
    expected_experiment_manifest: str | None = None,
) -> str:
    root = (
        active_data_root() if is_v6_experiment_id(run.experiment_id) else repository_root()
    )
    provenance = run.provenance
    if provenance is None:
        raise RuntimeError("Published versioned run has no provenance")
    derived_manifest = experiment_manifest_name(run.experiment_id)
    manifest_name = provenance.experiment_manifest or derived_manifest
    if manifest_name != derived_manifest:
        raise RuntimeError("Published experiment manifest does not match its run ID")
    if (
        expected_experiment_manifest is not None
        and manifest_name != expected_experiment_manifest
    ):
        raise RuntimeError("Published experiment manifest does not match the request")
    validate_experiment_manifest(root, manifest_name)
    manifest = load_experiment_manifest(root, manifest_name)
    if run.experiment_id != manifest["experiment_id"]:
        raise RuntimeError("Published experiment ID does not match its manifest")
    expected_manifest_hash = sha256_file(
        root / "data" / "experiments" / manifest_name
    )
    if provenance.freeze_tag != manifest["freeze_tag"]:
        raise RuntimeError("Published freeze tag mismatch")
    if provenance.prompt_hashes != manifest["prompt_hashes"]:
        raise RuntimeError("Published role prompt hashes mismatch")
    if provenance.prompt_version != manifest["prompt_version"]:
        raise RuntimeError("Published prompt version mismatch")
    if provenance.input_manifest_sha256 != expected_manifest_hash:
        raise RuntimeError("Published input manifest hash mismatch")
    if provenance.artifact_store != "gcs":
        raise RuntimeError("Published run was not written through the GCS run store")
    if not provenance.cloud_execution:
        raise RuntimeError("Published run has no Cloud Run execution ID")
    if (
        not provenance.container_image_digest
        or "@sha256:" not in provenance.container_image_digest
    ):
        raise RuntimeError("Published run has no immutable container image digest")
    if not provenance.adk_version:
        raise RuntimeError("Published run has no ADK version")
    if run.model != manifest["generation"]["model"]:
        raise RuntimeError("Published generation model mismatch")
    if run.embedding_model != manifest["retrieval"]["embedding_model"]:
        raise RuntimeError("Published embedding model mismatch")
    if run.experiment_id.startswith(
        ("ecr-poc-preregistered-v5", "ecr-poc-preregistered-v6")
    ) or is_v6_experiment_id(run.experiment_id):
        embedding_index_file = str(manifest["embedding_index_file"])
        if provenance.embedding_index_manifest != embedding_index_file:
            raise RuntimeError("Published embedding index manifest mismatch")
        if provenance.embedding_index_manifest_sha256 != sha256_file(
            root / embedding_index_file
        ):
            raise RuntimeError("Published embedding index manifest hash mismatch")
        if not provenance.embedding_index_fingerprint:
            raise RuntimeError("Published run has no embedding vector fingerprint")
    if is_v6_experiment_id(run.experiment_id):
        identifier_index_file = str(manifest["identifier_index_file"])
        if provenance.identifier_index_manifest != identifier_index_file:
            raise RuntimeError("Published identifier index manifest mismatch")
        if provenance.identifier_index_manifest_sha256 != sha256_file(
            root / identifier_index_file
        ):
            raise RuntimeError("Published identifier index manifest hash mismatch")
        if not provenance.identifier_index_fingerprint:
            raise RuntimeError("Published run has no identifier index fingerprint")
    return manifest_name


def _validated_run(
    content: bytes,
    *,
    require_cloud: bool = False,
    expected_experiment_manifest: str | None = None,
) -> EvaluationRun:
    run = EvaluationRun.model_validate_json(content)
    is_current_v6 = is_v6_experiment_id(run.experiment_id)
    is_versioned = is_current_v6 or (
        run.experiment_id.startswith("ecr-poc-preregistered-v")
        and run.experiment_id != "ecr-poc-preregistered-v1"
    )
    if require_cloud:
        if not is_versioned:
            raise RuntimeError("Published Cloud run is not a versioned experiment")
        _validate_cloud_provenance(run, expected_experiment_manifest)
    recalculated = calculate_metrics(
        run.cases,
        complete_overall=run.experiment_id.startswith("ecr-poc-preregistered-v5"),
    )
    if run.metrics != recalculated:
        raise RuntimeError("Published evaluation metrics do not match raw cases")
    expected_cases = 20 if is_current_v6 else 18
    if len(run.cases) != expected_cases:
        raise RuntimeError(
            f"Published evaluation is not a complete {expected_cases}-case run"
        )
    for case in run.cases:
        if is_versioned and case.run_id != run.run_id:
            raise RuntimeError(f"{case.case_id} does not use the evaluation run ID")
        if is_versioned and (
            case.provider != run.provider
            or case.model != run.model
            or case.embedding_model != run.embedding_model
        ):
            raise RuntimeError(f"{case.case_id} runtime provider/model identity mismatch")
        candidate_ids = [candidate.source_id for candidate in case.candidates]
        if len(candidate_ids) != int(run.configuration["top_k"]):
            raise RuntimeError(f"{case.case_id} does not contain the fixed Top-K")
        if not is_current_v6 and (
            case.baseline_candidate_source_ids != candidate_ids
            or case.proposed_candidate_source_ids != candidate_ids
        ):
            raise RuntimeError(f"{case.case_id} Baseline/Proposed arms differ")
        if case.candidate_fingerprint != candidate_fingerprint(case.candidates):
            raise RuntimeError(f"{case.case_id} candidate fingerprint mismatch")
        candidate_by_id = {
            candidate.source_id: candidate for candidate in case.candidates
        }
        if (
            run.experiment_id.startswith(
                ("ecr-poc-preregistered-v5", "ecr-poc-preregistered-v6")
            )
            or is_current_v6
        ) and (
                not case.embedding_index_fingerprint
                or case.embedding_index_fingerprint
                != run.configuration.get("embedding_index_fingerprint")
                or run.provenance is None
                or case.embedding_index_fingerprint
                != run.provenance.embedding_index_fingerprint
        ):
            raise RuntimeError(f"{case.case_id} embedding index fingerprint mismatch")
        if is_current_v6:
            if (
                case.query_processing is None
                or case.retrieval is None
                or case.retrieval.final_docket_fingerprint != case.candidate_fingerprint
                or case.retrieval.final_k != 10
                or case.retrieval.broad_k != 40
                or case.retrieval.expanded_count > 200
            ):
                raise RuntimeError(f"{case.case_id} retrieval seal mismatch")
            if (
                not case.identifier_index_fingerprint
                or case.identifier_index_fingerprint
                != run.configuration.get("identifier_index_fingerprint")
                or run.provenance is None
                or case.identifier_index_fingerprint
                != run.provenance.identifier_index_fingerprint
            ):
                raise RuntimeError(f"{case.case_id} identifier index fingerprint mismatch")
            result_counts = Counter(item.source_id for item in case.candidate_results)
            if set(result_counts) != set(candidate_ids) or any(
                count != 1 for count in result_counts.values()
            ):
                raise RuntimeError(f"{case.case_id} candidate result cardinality mismatch")
            verification_counts = Counter(
                item.claim_id for item in case.claim_verifications
            )
            for candidate_result in case.candidate_results:
                candidate = candidate_by_id.get(candidate_result.source_id)
                if candidate is None:
                    raise RuntimeError(f"{case.case_id} candidate result is off docket")
                if (
                    candidate_result.status is CandidateFinalStatus.VERIFIED_REVIEW
                    and not candidate_result.verified_claims
                ):
                    raise RuntimeError(f"{case.case_id} verified candidate has no claim")
                if (
                    candidate_result.status is not CandidateFinalStatus.VERIFIED_REVIEW
                    and candidate_result.verified_claims
                ):
                    raise RuntimeError(f"{case.case_id} unsupported claim was exposed")
                for claim in candidate_result.verified_claims:
                    matching = [
                        item
                        for item in case.claim_verifications
                        if item.claim_id == claim.claim_id
                    ]
                    if (
                        claim.source_id != candidate.source_id
                        or claim.evidence_exact_text not in candidate.content
                        or claim.evidence_start_line < candidate.start_line
                        or claim.evidence_end_line > candidate.end_line
                        or verification_counts[claim.claim_id] != 1
                        or matching[0].verdict is not VerifierVerdict.SUPPORTED
                    ):
                        raise RuntimeError(
                            f"{case.case_id} exposes an unsupported verified claim"
                        )
            if any(trace.error for trace in case.role_traces):
                raise RuntimeError(f"{case.case_id} contains a role error")
            continue
        verifier_items: list[dict[str, Any]] = []
        for trace in case.role_traces:
            if trace.role != "evidence_verifier" or not isinstance(trace.parsed, dict):
                continue
            values = trace.parsed.get("verifications")
            if isinstance(values, list):
                verifier_items.extend(item for item in values if isinstance(item, dict))
        verified_counts = Counter(
            review.source_id
            for review in case.final_reviews
            if review.status is FinalStatus.VERIFIED_REVIEW
        )
        if any(count != 1 for count in verified_counts.values()):
            raise RuntimeError(f"{case.case_id} contains duplicate verified reviews")
        for review in case.final_reviews:
            if review.status is not FinalStatus.VERIFIED_REVIEW:
                continue
            candidate = candidate_by_id.get(review.source_id)
            if (
                candidate is None
                or not review.evidence
                or review.evidence not in candidate.content
                or not review.short_reason
                or not review.verifier_reason
            ):
                raise RuntimeError(f"{case.case_id} exposes an unsupported verified review")
            if is_versioned:
                matching_verdicts = [
                    item
                    for item in verifier_items
                    if item.get("source_id") == review.source_id
                ]
                if (
                    len(matching_verdicts) != 1
                    or matching_verdicts[0].get("supported") is not True
                ):
                    raise RuntimeError(
                        f"{case.case_id} verified review lacks one supported verifier verdict"
                    )
        if any(trace.error for trace in case.role_traces):
            raise RuntimeError(f"{case.case_id} contains a role error")
    return run


def validate_historical_runs(root: Path | None = None) -> dict[str, str]:
    root = root or repository_root()
    files = {
        "v1": ("vertex-adk.json", None),
        "v2": ("vertex-adk-v2.json", "ecr-poc-v2.json"),
        "v3": ("vertex-adk-v3.json", "ecr-poc-v3.json"),
        "v4": ("vertex-adk-v4.json", "ecr-poc-v4.json"),
        "v5": ("vertex-adk-v5.json", "ecr-poc-v5.json"),
        "v5-q1": ("vertex-adk-v5-q1.json", "ecr-poc-v5-q1.json"),
    }
    validated: dict[str, str] = {}
    for version_label, (file_name, manifest_name) in files.items():
        content = (root / "results" / "runs" / file_name).read_bytes()
        run = _validated_run(
            content,
            require_cloud=manifest_name is not None,
            expected_experiment_manifest=manifest_name,
        )
        validated[version_label] = run.run_id
    return validated


def publish_run(
    bucket_name: str,
    run_id: str,
    source_commit: str,
    experiment_manifest: str,
    *,
    run_prefix: str = "runs/v6",
    published_object_name: str = "published/v6/demo.json",
) -> PublishedPointer:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    normalized_run_prefix = run_prefix.strip("/")
    result_parent = f"{normalized_run_prefix}/{run_id}"
    failure_blob = bucket.blob(f"{result_parent}/failure.json")
    if failure_blob.exists():
        raise RuntimeError("Failed runs cannot be published")
    result_name = f"{result_parent}/evaluation.json"
    result_blob = bucket.blob(result_name)
    content = result_blob.download_as_bytes()
    result_blob.reload()
    checkpoint_content = bucket.blob(
        f"{result_parent}/checkpoint.json"
    ).download_as_bytes()
    checkpoint = json.loads(checkpoint_content)
    final_record = checkpoint.get("final") if isinstance(checkpoint, dict) else None
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("status") != "complete"
        or not isinstance(final_record, dict)
        or final_record.get("generation") != int(result_blob.generation)
        or final_record.get("sha256") != hashlib.sha256(content).hexdigest()
    ):
        raise RuntimeError("Run completion checkpoint does not seal evaluation.json")
    run = _validated_run(
        content,
        require_cloud=True,
        expected_experiment_manifest=experiment_manifest,
    )
    if run.run_id != run_id:
        raise RuntimeError("Run ID does not match its GCS object path")
    if run.provenance is None or run.provenance.source_commit != source_commit:
        raise RuntimeError("Run source commit does not match publish request")
    pointer = PublishedPointer(
        run_id=run_id,
        experiment_id=run.experiment_id,
        object_name=result_name,
        generation=int(result_blob.generation),
        sha256=hashlib.sha256(content).hexdigest(),
        published_at=datetime.now(UTC).isoformat(),
        source_commit=source_commit,
        experiment_manifest=experiment_manifest,
    )
    pointer_blob = bucket.blob(published_object_name.strip("/"))
    pointer_generation = 0
    if pointer_blob.exists():
        pointer_blob.reload()
        pointer_generation = int(pointer_blob.generation)
    pointer_blob.upload_from_string(
        json_bytes(pointer.model_dump(mode="json")),
        content_type="application/json",
        if_generation_match=pointer_generation,
    )
    log_event(
        "run_published",
        run_id=run_id,
    )
    return pointer


def load_published_run(
    bucket_name: str,
    published_object_name: str = "published/v6/demo.json",
) -> tuple[EvaluationRun, PublishedPointer]:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    pointer_content = bucket.blob(
        published_object_name.strip("/")
    ).download_as_bytes()
    pointer = PublishedPointer.model_validate_json(pointer_content)
    result_blob = bucket.blob(pointer.object_name, generation=pointer.generation)
    content = result_blob.download_as_bytes(if_generation_match=pointer.generation)
    if hashlib.sha256(content).hexdigest() != pointer.sha256:
        raise RuntimeError("Published result SHA-256 mismatch")
    expected_manifest = pointer.experiment_manifest or experiment_manifest_name(
        pointer.experiment_id
    )
    if (
        pointer.experiment_id != "ecr-poc-preregistered-v2"
        and not pointer.experiment_manifest
    ):
        raise RuntimeError("Published v3 pointer has no experiment manifest")
    run = _validated_run(
        content,
        require_cloud=True,
        expected_experiment_manifest=expected_manifest,
    )
    if run.run_id != pointer.run_id or run.experiment_id != pointer.experiment_id:
        raise RuntimeError("Published pointer identity mismatch")
    if (
        not pointer.object_name.endswith(f"/{run.run_id}/evaluation.json")
        or run.provenance is None
        or pointer.source_commit != run.provenance.source_commit
        or expected_manifest
        != (run.provenance.experiment_manifest or experiment_manifest_name(run.experiment_id))
    ):
        raise RuntimeError("Published pointer provenance mismatch")
    return run, pointer
