from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import (
    load_artifacts,
    load_cases,
    repository_root,
    validate_all,
    validate_freeze,
)
from .metrics import calculate_metrics
from .models import EvaluationRun
from .pipeline import run_case
from .providers import AdkVertexProvider, FixtureProvider, ReviewProvider
from .retrieval import HybridRetriever, build_embedder


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_provider(name: str, inject_unsupported: bool = False) -> ReviewProvider:
    if name == "vertex-adk":
        return AdkVertexProvider(os.environ.get("ECR_LLM_MODEL", "gemini-3.5-flash"))
    if name == "fixture":
        return FixtureProvider(inject_unsupported=inject_unsupported)
    raise ValueError(f"Unknown review provider: {name}")


async def evaluate(
    provider_name: str,
    embedding_provider: str,
    output_path: Path | None = None,
    inject_unsupported: bool = False,
) -> EvaluationRun:
    root = repository_root()
    validate_all(root)
    freeze_hashes = validate_freeze(root)
    experiment_id, top_k, cases = load_cases(root)
    artifacts = load_artifacts(root)
    embedder = build_embedder(embedding_provider)
    retriever = HybridRetriever(artifacts, embedder)
    provider = build_provider(provider_name, inject_unsupported=inject_unsupported)
    started_at = _now()
    run_id = str(uuid.uuid4())
    if output_path is None:
        output_path = root / "results" / "runs" / f"{run_id}.json"
    elif not output_path.is_absolute():
        output_path = root / output_path
    checkpoint_path = output_path.with_suffix(".checkpoint.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    case_results = []
    for case in cases:
        try:
            case_results.append(await run_case(case, retriever, provider, top_k))
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
            }
            with checkpoint_path.open("w", encoding="utf-8") as handle:
                json.dump(failure_checkpoint, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            raise
        checkpoint: dict[str, Any] = {
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
        }
        with checkpoint_path.open("w", encoding="utf-8") as handle:
            json.dump(checkpoint, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
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
            "fail_closed": True,
            "case_attempt_policy": "one attempt; role failure is recorded and exposes no review advice",
            "checkpoint_after_each_case": str(checkpoint_path.relative_to(root)),
            "inject_unsupported_fixture": inject_unsupported,
        },
        cases=case_results,
        metrics=calculate_metrics(case_results),
    )
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(run.model_dump(mode="json"), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    checkpoint["status"] = "complete"
    checkpoint["completed_at"] = completed_at
    checkpoint["metrics"] = run.metrics
    with checkpoint_path.open("w", encoding="utf-8") as handle:
        json.dump(checkpoint, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    latest = root / "results" / "latest.json"
    with latest.open("w", encoding="utf-8") as handle:
        json.dump(run.model_dump(mode="json"), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return run
