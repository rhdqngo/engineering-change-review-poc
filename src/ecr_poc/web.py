from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data import (
    ACTIVE_EXPERIMENT_ID,
    active_data_root,
    active_experiment_manifest,
    load_artifacts,
    load_cases,
    load_experiment_manifest,
    validate_all,
)
from .embedding_index import load_embedding_index
from .evaluation import build_provider
from .identifier_index import load_identifier_index
from .models import (
    CaseDefinition,
    IncomingArtifact,
    LiveReviewRequest,
    LiveReviewResponse,
)
from .observability import log_event
from .pipeline import run_case
from .prompts import load_prompt_bundle
from .providers import FixtureProvider, ReviewProvider
from .retrieval import DeterministicHashEmbedder, HybridRetriever, build_embedder
from .storage import load_published_run, materialize_gcs_prefix

STATIC_DIR = Path(__file__).parent / "static"
_PUBLISHED_CACHE_LOCK = threading.Lock()
_PUBLISHED_CACHE: tuple[
    float, str, dict[str, object], dict[str, str]
] | None = None
_LIVE_EXECUTION_LOCK = threading.Lock()
_LIVE_RUNTIME_LOCK = threading.Lock()
_LIVE_RUNTIME: LiveRuntime | None = None
_RUNTIME_DATA_ROOT: Path | None = None


@dataclass(frozen=True)
class LiveRuntime:
    baseline_id: str
    top_k: int
    retriever: HybridRetriever
    provider: ReviewProvider


def _runtime_data_root() -> Path:
    global _RUNTIME_DATA_ROOT
    if _RUNTIME_DATA_ROOT is not None:
        return _RUNTIME_DATA_ROOT
    if os.environ.get("ECR_RESULT_STORE", "local") != "gcs":
        _RUNTIME_DATA_ROOT = active_data_root()
        return _RUNTIME_DATA_ROOT
    bucket = os.environ.get("ECR_GCS_BUCKET")
    prefix = os.environ.get("ECR_GCS_INPUT_PREFIX")
    if not bucket or not prefix:
        raise RuntimeError("GCS runtime requires ECR_GCS_BUCKET and ECR_GCS_INPUT_PREFIX")
    target = Path(tempfile.mkdtemp(prefix="ecr-poc-v6-"))
    materialize_gcs_prefix(bucket, prefix, target)
    _RUNTIME_DATA_ROOT = target
    os.environ["ECR_DATA_ROOT"] = str(target)
    return target


def _build_live_runtime() -> LiveRuntime:
    root = _runtime_data_root()
    manifest_name = active_experiment_manifest()
    validate_all(root, manifest_name)
    manifest = load_experiment_manifest(root, manifest_name)
    artifacts = load_artifacts(root, manifest_name)
    metadata_relative = str(manifest["embedding_index_file"])
    frozen_index = load_embedding_index(root, metadata_relative, artifacts)
    embedding_provider = os.environ.get("ECR_LIVE_EMBEDDING", "local")
    embedder = build_embedder(embedding_provider)
    if embedder.model_name != frozen_index.model_name:
        if (
            os.environ.get("ECR_LIVE_PROVIDER", "fixture") == "fixture"
            and embedding_provider == "local"
        ):
            embedder = DeterministicHashEmbedder(frozen_index.dimensions)
        else:
            raise RuntimeError("Live query embedding model does not match the frozen index")
    retriever = HybridRetriever(
        artifacts,
        embedder,
        document_embeddings=frozen_index.vectors,
        embedding_index_fingerprint=frozen_index.fingerprint,
        identifier_index=load_identifier_index(
            root / str(manifest["identifier_index_file"]),
            artifacts,
            expected_artifact_package_sha256=str(
                manifest["files"][str(manifest["artifact_package_file"])]
            ),
            expected_sha256=str(
                manifest["files"][str(manifest["identifier_index_file"])]
            ),
        ),
    )
    prompt_bundle = load_prompt_bundle(root, str(manifest["prompt_file"]))
    provider = build_provider(
        os.environ.get("ECR_LIVE_PROVIDER", "fixture"),
        prompt_bundle=prompt_bundle,
    )
    return LiveRuntime(
        baseline_id=str(manifest["baseline_id"]),
        top_k=int(manifest["top_k"]),
        retriever=retriever,
        provider=provider,
    )


def _live_runtime() -> LiveRuntime:
    global _LIVE_RUNTIME
    if _LIVE_RUNTIME is not None:
        return _LIVE_RUNTIME
    with _LIVE_RUNTIME_LOCK:
        if _LIVE_RUNTIME is None:
            _LIVE_RUNTIME = _build_live_runtime()
    return _LIVE_RUNTIME

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
    root = Path(__file__).resolve().parents[2]
    active_result = root / "results" / "runs" / "fixture-v6-baseline.json"
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
            os.environ.get("ECR_PUBLISHED_OBJECT", "published/v6/demo.json"),
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
        _runtime_data_root()
        bucket = os.environ.get("ECR_GCS_BUCKET")
        if not bucket:
            raise RuntimeError("ECR_GCS_BUCKET is required when ECR_RESULT_STORE=gcs")
        run, pointer = load_published_run(
            bucket,
            os.environ.get("ECR_PUBLISHED_OBJECT", "published/v6/demo.json"),
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
            "identifier_index_fingerprint": (
                run.provenance.identifier_index_fingerprint
                if run.provenance and run.provenance.identifier_index_fingerprint
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
        "identifier_index_fingerprint": str(
            provenance.get("identifier_index_fingerprint", "")
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
        validate_all(await asyncio.to_thread(_runtime_data_root))
        _, metadata = await _published_evaluation()
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"integrity check failed: {error}") from error
    return {"status": "ready", "data_integrity": "valid", **metadata}


@app.get("/integrity")
async def integrity() -> dict[str, object]:
    try:
        root = await asyncio.to_thread(_runtime_data_root)
        counts = validate_all(root)
        payload, metadata = await _published_evaluation()
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"integrity check failed: {error}") from error
    published_cases = payload.get("cases")
    manifest = load_experiment_manifest(root, active_experiment_manifest())
    return {
        "status": "valid",
        "active_experiment_id": str(manifest["experiment_id"]),
        "data": counts,
        "published_cases": len(published_cases) if isinstance(published_cases, list) else 0,
        **metadata,
    }


@app.get("/api/cases")
async def cases() -> dict[str, object]:
    root = await asyncio.to_thread(_runtime_data_root)
    experiment_id, top_k, frozen_cases = load_cases(root, active_experiment_manifest())
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
    root = await asyncio.to_thread(_runtime_data_root)
    _, top_k, frozen_cases = load_cases(root)
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

    retriever = (await asyncio.to_thread(_live_runtime)).retriever
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


def _live_case(request_id: str, incoming: IncomingArtifact) -> CaseDefinition:
    label = incoming.title or incoming.subsystem or incoming.artifact_type.value
    return CaseDefinition(
        id=f"LIVE-{request_id}",
        type="live",
        scenario=label,
        incoming_artifact=incoming,
        expected_review_targets=[],
    )


@app.post("/api/reviews", response_model=LiveReviewResponse)
async def create_review(payload: LiveReviewRequest) -> LiveReviewResponse:
    if not _LIVE_EXECUTION_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Another engineering review is running")
    request_id = str(uuid.uuid4())
    started = time.monotonic()
    try:
        try:
            runtime = await asyncio.to_thread(_live_runtime)
        except Exception as error:
            log_event(
                "live_review_unavailable",
                severity="ERROR",
                request_id=request_id,
                artifact_type=payload.incoming_artifact.artifact_type,
                blocked_stage="embedding_index_readiness",
                error_type=type(error).__name__,
            )
            raise HTTPException(status_code=503, detail="Review index is not ready") from error
        case = _live_case(request_id, payload.incoming_artifact)
        try:
            result = await run_case(
                case,
                runtime.retriever,
                runtime.provider,
                runtime.top_k,
                evaluation_run_id=request_id,
            )
        except TimeoutError as error:
            raise HTTPException(status_code=504, detail="Query embedding timed out") from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="Query embedding failed") from error
        assert result.overall_status is not None
        assert result.embedding_index_fingerprint is not None
        assert result.identifier_index_fingerprint is not None
        assert result.query_processing is not None
        assert result.retrieval is not None
        verified = sum(
            review.status == "VERIFIED_REVIEW" for review in result.candidate_results
        )
        blocked = sum(review.blocked_count for review in result.candidate_results)
        log_event(
            "live_review_completed",
            request_id=request_id,
            artifact_type=payload.incoming_artifact.artifact_type,
            model=result.model,
            overall_status=result.overall_status,
            candidate_fingerprint=result.candidate_fingerprint,
            verified=verified,
            blocked=blocked,
            latency_ms=round((time.monotonic() - started) * 1000),
        )
        return LiveReviewResponse(
            request_id=request_id,
            baseline_id=runtime.baseline_id,
            provider=result.provider,
            model=result.model,
            embedding_model=result.embedding_model,
            embedding_index_fingerprint=result.embedding_index_fingerprint,
            identifier_index_fingerprint=result.identifier_index_fingerprint,
            query_processing=result.query_processing,
            retrieval=result.retrieval,
            final_docket=result.candidates,
            candidate_results=result.candidate_results,
            overall_status=result.overall_status,
            partial=result.partial,
        )
    finally:
        _LIVE_EXECUTION_LOCK.release()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/evaluation")
async def evaluation_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "evaluation.html")
