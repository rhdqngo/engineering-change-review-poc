from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .data import (
    load_artifacts,
    load_cases,
    load_experiment_manifest,
    repository_root,
    sha256_file,
    validate_all,
    validate_experiment_manifest,
    validate_freeze,
)
from .metrics import calculate_metrics
from .models import EvaluationRun, RunProvenance
from .observability import log_event
from .pipeline import run_case
from .prompts import PromptBundle, load_prompt_bundle
from .providers import AdkVertexProvider, FixtureProvider, ReviewProvider
from .retrieval import HybridRetriever, build_embedder
from .storage import LocalRunStore, RunStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _record_failure(
    run_store: RunStore,
    payload: dict[str, Any],
    error: Exception,
    *,
    run_id: str,
    case_id: str | None,
    blocked_stage: str,
) -> None:
    failure_write_error: Exception | None = None
    try:
        run_store.write_failure(payload)
    except Exception as store_error:  # noqa: BLE001 - preserve the primary failure
        failure_write_error = store_error
    log_event(
        "job_failed",
        severity="ERROR",
        run_id=run_id,
        case_id=case_id,
        blocked_stage=blocked_stage,
        error_type=type(error).__name__,
        failure_write_error_type=(
            type(failure_write_error).__name__ if failure_write_error else None
        ),
    )


def build_provider(
    name: str,
    inject_unsupported: bool = False,
    prompt_bundle: PromptBundle | None = None,
) -> ReviewProvider:
    if name == "vertex-adk":
        return AdkVertexProvider(
            os.environ.get("ECR_LLM_MODEL", "gemini-3.5-flash"), prompt_bundle
        )
    if name == "fixture":
        return FixtureProvider(inject_unsupported=inject_unsupported)
    raise ValueError(f"Unknown review provider: {name}")


async def evaluate(
    provider_name: str,
    embedding_provider: str,
    output_path: Path | None = None,
    inject_unsupported: bool = False,
    *,
    root: Path | None = None,
    run_id: str | None = None,
    run_store: RunStore | None = None,
    experiment_manifest: str | None = None,
    source_commit: str | None = None,
    cloud_execution: str | None = None,
    container_image_digest: str | None = None,
    role_timeout_seconds: float | None = None,
    update_latest: bool = True,
) -> EvaluationRun:
    root = root or repository_root()
    validate_all(root)
    freeze_hashes = validate_freeze(root)
    base_experiment_id, top_k, cases = load_cases(root)
    experiment_id = base_experiment_id
    provenance: RunProvenance | None = None
    manifest: dict[str, Any] | None = None
    prompt_file = "data/prompts/ecr-poc-v2.json"
    if experiment_manifest:
        validate_experiment_manifest(root, experiment_manifest)
        manifest = load_experiment_manifest(root, experiment_manifest)
        experiment_id = str(manifest["experiment_id"])
        if not source_commit:
            raise RuntimeError("Versioned evaluation requires a source commit")
        prompt_file = str(manifest["prompt_file"])
    prompt_bundle = load_prompt_bundle(root, prompt_file)
    if manifest is not None:
        assert experiment_manifest is not None
        assert source_commit is not None
        prompt_hashes = {
            str(role): str(digest)
            for role, digest in manifest["prompt_hashes"].items()
        }
        provenance = RunProvenance(
            source_commit=source_commit,
            freeze_tag=str(manifest["freeze_tag"]),
            experiment_manifest=experiment_manifest,
            prompt_version=prompt_bundle.version,
            prompt_hashes=prompt_hashes,
            input_manifest_sha256=sha256_file(
                root / "data" / "experiments" / experiment_manifest
            ),
            artifact_store=run_store.kind if run_store else "local",
            cloud_execution=cloud_execution,
            container_image_digest=container_image_digest,
            adk_version=version("google-adk"),
        )
    artifacts = load_artifacts(root)
    embedder = build_embedder(embedding_provider)
    retriever = HybridRetriever(artifacts, embedder)
    provider = build_provider(
        provider_name,
        inject_unsupported=inject_unsupported,
        prompt_bundle=prompt_bundle,
    )
    started_at = _now()
    run_id = run_id or str(uuid.uuid4())
    if run_store is None:
        if output_path is None:
            output_path = root / "results" / "runs" / f"{run_id}.json"
        elif not output_path.is_absolute():
            output_path = root / output_path
        run_store = LocalRunStore(
            output_path,
            update_latest=update_latest,
            latest_path=root / "results" / "latest.json",
        )
        if provenance is not None:
            provenance.artifact_store = run_store.kind
    timeout = role_timeout_seconds
    if timeout is None:
        timeout = float(
            os.environ.get(
                "ECR_ROLE_TIMEOUT_SECONDS",
                str(manifest["generation"]["role_timeout_seconds"] if manifest else 120),
            )
        )
    log_event(
        "job_started",
        run_id=run_id,
        model=provider.model_name,
    )
    case_results = []
    checkpoint: dict[str, Any] = {}
    for case in cases:
        log_event("case_started", run_id=run_id, case_id=case.id)
        try:
            result = await run_case(
                case,
                retriever,
                provider,
                top_k,
                evaluation_run_id=run_id,
                role_timeout_seconds=timeout,
            )
            case_results.append(result)
        except Exception as error:
            failure_checkpoint: dict[str, Any] = {
                "status": "failed",
                "experiment_id": experiment_id,
                "run_id": run_id,
                "provider": provider.name,
                "model": provider.model_name,
                "embedding_model": embedder.model_name,
                "started_at": started_at,
                "failed_at": _now(),
                "freeze_hashes": freeze_hashes,
                "completed_case_ids": [item.case_id for item in case_results],
                "failed_case_id": case.id,
                "error": f"{type(error).__name__}: {error}",
                "cases": [item.model_dump(mode="json") for item in case_results],
                "provenance": provenance.model_dump(mode="json") if provenance else None,
            }
            _record_failure(
                run_store,
                failure_checkpoint,
                error,
                run_id=run_id,
                case_id=case.id,
                blocked_stage="case_execution",
            )
            raise
        checkpoint = {
            "status": "in_progress",
            "experiment_id": experiment_id,
            "run_id": run_id,
            "provider": provider.name,
            "model": provider.model_name,
            "embedding_model": embedder.model_name,
            "started_at": started_at,
            "freeze_hashes": freeze_hashes,
            "completed_case_ids": [item.case_id for item in case_results],
            "cases": [item.model_dump(mode="json") for item in case_results],
            "provenance": provenance.model_dump(mode="json") if provenance else None,
        }
        try:
            run_store.write_checkpoint(checkpoint)
        except Exception as error:
            failed_checkpoint = {
                **checkpoint,
                "status": "failed",
                "failed_at": _now(),
                "failed_case_id": case.id,
                "blocked_stage": "checkpoint_write",
                "error": f"{type(error).__name__}: {error}",
            }
            _record_failure(
                run_store,
                failed_checkpoint,
                error,
                run_id=run_id,
                case_id=case.id,
                blocked_stage="checkpoint_write",
            )
            raise
        log_event(
            "checkpoint_written",
            run_id=run_id,
            case_id=case.id,
            completed_cases=len(case_results),
        )
        verified = sum(
            item.status.value == "VERIFIED_REVIEW" for item in result.final_reviews
        )
        blocked = sum(
            item.status.value == "REJECTED_UNSUPPORTED" for item in result.final_reviews
        )
        log_event(
            "case_completed",
            run_id=run_id,
            case_id=case.id,
            candidate_fingerprint=result.candidate_fingerprint,
            verified=verified,
            blocked=blocked,
        )
    completed_at = _now()
    run = EvaluationRun(
        experiment_id=experiment_id,
        run_id=run_id,
        provider=provider.name,
        model=provider.model_name,
        embedding_model=embedder.model_name,
        started_at=started_at,
        completed_at=completed_at,
        freeze_hashes=freeze_hashes,
        configuration={
            "top_k": top_k,
            "lexical": "BM25(k1=1.5,b=0.75)",
            "fusion": {"bm25": 0.5, "embedding": 0.5, "normalization": "min-max"},
            "temperature": 0,
            "role_timeout_seconds": timeout,
            "fail_closed": True,
            "case_attempt_policy": "one attempt; a pre-retrieval failure fails the run and publishes nothing",
            "checkpoint_after_each_case": run_store.location,
            "inject_unsupported_fixture": inject_unsupported,
        },
        cases=case_results,
        metrics=calculate_metrics(case_results),
        provenance=provenance,
    )
    try:
        stored_final = run_store.write_final(run)
    except Exception as error:
        failed_final = {
            **checkpoint,
            "status": "failed",
            "failed_at": _now(),
            "blocked_stage": "evaluation_write",
            "error": f"{type(error).__name__}: {error}",
        }
        _record_failure(
            run_store,
            failed_final,
            error,
            run_id=run_id,
            case_id=None,
            blocked_stage="evaluation_write",
        )
        raise
    checkpoint["status"] = "complete"
    checkpoint["completed_at"] = completed_at
    checkpoint["metrics"] = run.metrics
    checkpoint["final"] = {
        "uri": stored_final.uri,
        "generation": stored_final.generation,
        "sha256": stored_final.sha256,
    }
    try:
        run_store.write_checkpoint(checkpoint)
    except Exception as error:
        failed_completion = {
            **checkpoint,
            "status": "failed",
            "failed_at": _now(),
            "blocked_stage": "completion_checkpoint_write",
            "error": f"{type(error).__name__}: {error}",
        }
        _record_failure(
            run_store,
            failed_completion,
            error,
            run_id=run_id,
            case_id=None,
            blocked_stage="completion_checkpoint_write",
        )
        raise
    log_event(
        "evaluation_completed",
        run_id=run_id,
        cases=len(case_results),
    )
    return run
