from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from .data import (
    load_experiment_manifest,
    repository_root,
    sha256_file,
    validate_experiment_manifest,
)
from .metrics import calculate_metrics
from .models import EvaluationRun, FinalStatus, PublishedPointer
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
    for relative in ["data/cases", "data/nasa", "data/experiments", "data/prompts"]:
        base = root / relative
        yield from (path for path in base.rglob("*") if path.is_file())


def upload_frozen_tree(root: Path, bucket_name: str, prefix: str) -> dict[str, int]:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    uploaded = 0
    existing = 0
    for path in _frozen_paths(root):
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
    return {"uploaded": uploaded, "verified_existing": existing}


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


def _validate_cloud_v2_provenance(run: EvaluationRun) -> None:
    root = repository_root()
    validate_experiment_manifest(root)
    manifest = load_experiment_manifest(root)
    provenance = run.provenance
    if provenance is None:
        raise RuntimeError("Published v2 run has no provenance")
    expected_manifest_hash = sha256_file(
        root / "data" / "experiments" / "ecr-poc-v2.json"
    )
    if provenance.freeze_tag != manifest["freeze_tag"]:
        raise RuntimeError("Published v2 freeze tag mismatch")
    if provenance.prompt_hashes != manifest["prompt_hashes"]:
        raise RuntimeError("Published v2 role prompt hashes mismatch")
    if provenance.prompt_version != manifest["prompt_version"]:
        raise RuntimeError("Published v2 prompt version mismatch")
    if provenance.input_manifest_sha256 != expected_manifest_hash:
        raise RuntimeError("Published v2 input manifest hash mismatch")
    if provenance.artifact_store != "gcs":
        raise RuntimeError("Published v2 run was not written through the GCS run store")
    if not provenance.cloud_execution:
        raise RuntimeError("Published v2 run has no Cloud Run execution ID")
    if (
        not provenance.container_image_digest
        or "@sha256:" not in provenance.container_image_digest
    ):
        raise RuntimeError("Published v2 run has no immutable container image digest")
    if not provenance.adk_version:
        raise RuntimeError("Published v2 run has no ADK version")
    if run.model != manifest["generation"]["model"]:
        raise RuntimeError("Published v2 generation model mismatch")
    if run.embedding_model != manifest["retrieval"]["embedding_model"]:
        raise RuntimeError("Published v2 embedding model mismatch")


def _validated_run(content: bytes, *, require_cloud_v2: bool = False) -> EvaluationRun:
    run = EvaluationRun.model_validate_json(content)
    if require_cloud_v2 and run.experiment_id == "ecr-poc-preregistered-v2":
        _validate_cloud_v2_provenance(run)
    recalculated = calculate_metrics(run.cases)
    if run.metrics != recalculated:
        raise RuntimeError("Published evaluation metrics do not match raw cases")
    if len(run.cases) != 18:
        raise RuntimeError("Published evaluation is not a complete 18-case run")
    for case in run.cases:
        if run.experiment_id == "ecr-poc-preregistered-v2" and case.run_id != run.run_id:
            raise RuntimeError(f"{case.case_id} does not use the evaluation run ID")
        if run.experiment_id == "ecr-poc-preregistered-v2" and (
            case.provider != run.provider
            or case.model != run.model
            or case.embedding_model != run.embedding_model
        ):
            raise RuntimeError(f"{case.case_id} runtime provider/model identity mismatch")
        candidate_ids = [candidate.source_id for candidate in case.candidates]
        if len(candidate_ids) != int(run.configuration["top_k"]):
            raise RuntimeError(f"{case.case_id} does not contain the fixed Top-K")
        if (
            case.baseline_candidate_source_ids != candidate_ids
            or case.proposed_candidate_source_ids != candidate_ids
        ):
            raise RuntimeError(f"{case.case_id} Baseline/Proposed arms differ")
        if case.candidate_fingerprint != candidate_fingerprint(case.candidates):
            raise RuntimeError(f"{case.case_id} candidate fingerprint mismatch")
        candidate_by_id = {candidate.source_id: candidate for candidate in case.candidates}
        verifier_items: list[dict[str, Any]] = []
        for trace in case.role_traces:
            if trace.role != "evidence_verifier" or not isinstance(trace.parsed, dict):
                continue
            values = trace.parsed.get("verifications")
            if isinstance(values, list):
                verifier_items.extend(item for item in values if isinstance(item, dict))
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
            if run.experiment_id == "ecr-poc-preregistered-v2":
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


def publish_run(bucket_name: str, run_id: str, source_commit: str) -> PublishedPointer:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    failure_blob = bucket.blob(f"runs/{run_id}/failure.json")
    if failure_blob.exists():
        raise RuntimeError("Failed runs cannot be published")
    result_name = f"runs/{run_id}/evaluation.json"
    result_blob = bucket.blob(result_name)
    content = result_blob.download_as_bytes()
    result_blob.reload()
    checkpoint_content = bucket.blob(
        f"runs/{run_id}/checkpoint.json"
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
    run = _validated_run(content, require_cloud_v2=True)
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
    )
    pointer_blob = bucket.blob("published/demo.json")
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


def load_published_run(bucket_name: str) -> tuple[EvaluationRun, PublishedPointer]:
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    pointer_content = bucket.blob("published/demo.json").download_as_bytes()
    pointer = PublishedPointer.model_validate_json(pointer_content)
    result_blob = bucket.blob(pointer.object_name, generation=pointer.generation)
    content = result_blob.download_as_bytes(if_generation_match=pointer.generation)
    if hashlib.sha256(content).hexdigest() != pointer.sha256:
        raise RuntimeError("Published result SHA-256 mismatch")
    run = _validated_run(content, require_cloud_v2=True)
    if run.run_id != pointer.run_id or run.experiment_id != pointer.experiment_id:
        raise RuntimeError("Published pointer identity mismatch")
    if run.experiment_id == "ecr-poc-preregistered-v2" and (
        pointer.object_name != f"runs/{run.run_id}/evaluation.json"
        or run.provenance is None
        or pointer.source_commit != run.provenance.source_commit
    ):
        raise RuntimeError("Published v2 pointer provenance mismatch")
    return run, pointer
