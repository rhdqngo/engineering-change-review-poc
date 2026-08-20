from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data import (
    ACTIVE_EXPERIMENT_ID,
    load_artifacts,
    load_cases,
    repository_root,
    validate_all,
)
from .pipeline import run_case
from .providers import FixtureProvider
from .retrieval import HybridRetriever, build_embedder
from .storage import load_published_run

STATIC_DIR = Path(__file__).parent / "static"
_PUBLISHED_CACHE_LOCK = threading.Lock()
_PUBLISHED_CACHE: tuple[
    float, str, dict[str, object], dict[str, str]
] | None = None

app = FastAPI(
    title="Evidence-grounded Engineering Change Review PoC",
    version="0.2.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def prevent_stale_evaluation_cache(request: Request, call_next) -> Response:
    response = await call_next(request)
    if (
        request.url.path in {"/health", "/healthz", "/readyz", "/integrity"}
        or request.url.path.startswith("/api/")
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


def _local_evaluation() -> dict[str, object]:
    root = repository_root()
    active_result = root / "results" / "runs" / "fixture-v5-baseline.json"
    path = active_result if active_result.exists() else root / "results" / "latest.json"
    if not path.exists():
        raise RuntimeError("no local published evaluation result")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("local published evaluation is not a JSON object")
    return value


def _published_evaluation_sync() -> tuple[dict[str, object], dict[str, str]]:
    global _PUBLISHED_CACHE
    now = time.monotonic()
    ttl = max(float(os.environ.get("ECR_PUBLISHED_CACHE_TTL_SECONDS", "30")), 0.0)
    cache_key = "|".join(
        [
            os.environ.get("ECR_RESULT_STORE", "local"),
            os.environ.get("ECR_GCS_BUCKET", ""),
            os.environ.get("ECR_PUBLISHED_OBJECT", "published/v5/demo.json"),
            os.environ.get("ECR_FREEZE_VERSION", ACTIVE_EXPERIMENT_ID),
        ]
    )
    cached = _PUBLISHED_CACHE
    if cached is not None and cached[1] == cache_key and now < cached[0]:
        return cached[2], cached[3]
    with _PUBLISHED_CACHE_LOCK:
        cached = _PUBLISHED_CACHE
        if cached is not None and cached[1] == cache_key and now < cached[0]:
            return cached[2], cached[3]
        payload, metadata = _load_published_evaluation_uncached()
        freeze_version = str(payload.get("experiment_id", "unknown"))
        expected_version = os.environ.get("ECR_FREEZE_VERSION", ACTIVE_EXPERIMENT_ID)
        if freeze_version != expected_version:
            raise RuntimeError(
                f"active runtime requires {expected_version}; received {freeze_version}"
            )
        _PUBLISHED_CACHE = (now + ttl, cache_key, payload, metadata)
        return payload, metadata


def _load_published_evaluation_uncached() -> tuple[dict[str, object], dict[str, str]]:
    result_store = os.environ.get("ECR_RESULT_STORE", "local")
    if result_store == "gcs":
        bucket = os.environ.get("ECR_GCS_BUCKET")
        if not bucket:
            raise RuntimeError("ECR_GCS_BUCKET is required when ECR_RESULT_STORE=gcs")
        run, pointer = load_published_run(
            bucket,
            os.environ.get("ECR_PUBLISHED_OBJECT", "published/v5/demo.json"),
        )
        return run.model_dump(mode="json"), {
            "result_store": "gcs",
            "published_run_id": pointer.run_id,
            "freeze_version": run.experiment_id,
            "source_commit": pointer.source_commit,
            "experiment_manifest": pointer.experiment_manifest or "",
            "embedding_index_fingerprint": (
                run.provenance.embedding_index_fingerprint
                if run.provenance and run.provenance.embedding_index_fingerprint
                else ""
            ),
        }
    if result_store != "local":
        raise RuntimeError(f"unknown result store: {result_store}")
    value = _local_evaluation()
    provenance = value.get("provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    return value, {
        "result_store": "local",
        "published_run_id": str(value.get("run_id", "unknown")),
        "freeze_version": str(value.get("experiment_id", "unknown")),
        "source_commit": str(provenance.get("source_commit", "")),
        "experiment_manifest": str(provenance.get("experiment_manifest", "")),
        "embedding_index_fingerprint": str(
            provenance.get("embedding_index_fingerprint", "")
        ),
    }


async def _published_evaluation() -> tuple[dict[str, object], dict[str, str]]:
    return await asyncio.to_thread(_published_evaluation_sync)


@app.get("/health")
@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/readyz")
async def readiness() -> dict[str, str]:
    try:
        validate_all()
        _, metadata = await _published_evaluation()
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"integrity check failed: {error}") from error
    return {"status": "ready", "data_integrity": "valid", **metadata}


@app.get("/integrity")
async def integrity() -> dict[str, object]:
    try:
        counts = validate_all()
        payload, metadata = await _published_evaluation()
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"integrity check failed: {error}") from error
    published_cases = payload.get("cases")
    return {
        "status": "valid",
        "active_experiment_id": ACTIVE_EXPERIMENT_ID,
        "data": counts,
        "published_cases": len(published_cases) if isinstance(published_cases, list) else 0,
        **metadata,
    }


@app.get("/api/cases")
async def cases() -> dict[str, object]:
    experiment_id, top_k, frozen_cases = load_cases()
    return {
        "experiment_id": experiment_id,
        "top_k": top_k,
        "cases": [case.model_dump(mode="json") for case in frozen_cases],
    }


def _case_from_payload(payload: dict[str, object], case_id: str) -> dict[str, object] | None:
    results = payload.get("cases")
    if not isinstance(results, list):
        return None
    for result in results:
        if isinstance(result, dict) and result.get("case_id") == case_id:
            return result
    return None


@app.get("/api/cases/{case_id}/result")
async def case_result(
    case_id: str,
    source: str = Query(default="fixture", pattern="^(fixture|latest|published)$"),
) -> dict[str, object]:
    _, top_k, frozen_cases = load_cases()
    case = next((item for item in frozen_cases if item.id == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail="unknown frozen case")
    if source in {"latest", "published"}:
        try:
            payload, metadata = await _published_evaluation()
        except Exception as error:
            raise HTTPException(
                status_code=503, detail=f"published evaluation unavailable: {error}"
            ) from error
        saved_result = _case_from_payload(payload, case_id)
        if saved_result is None:
            raise HTTPException(status_code=404, detail="no published result for case")
        return {
            "result_source": "published-evaluation",
            "result_metadata": metadata,
            "result": saved_result,
        }

    retriever = HybridRetriever(load_artifacts(), build_embedder("local"))
    provider = FixtureProvider(inject_unsupported=True)
    fixture_result = await run_case(case, retriever, provider, top_k)
    return {
        "result_source": "deterministic-fixture-not-llm-evidence",
        "result": fixture_result.model_dump(mode="json"),
    }


@app.get("/api/evaluation")
async def published_evaluation() -> dict[str, object]:
    try:
        payload, _ = await _published_evaluation()
    except Exception as error:
        raise HTTPException(
            status_code=503, detail=f"published evaluation unavailable: {error}"
        ) from error
    return payload


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
