from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data import load_artifacts, load_cases, repository_root, validate_all
from .pipeline import run_case
from .providers import FixtureProvider
from .retrieval import HybridRetriever, build_embedder

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Evidence-grounded Engineering Change Review PoC",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        validate_all()
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"data integrity failed: {error}") from error
    return {"status": "ok", "data_freeze": "valid"}


@app.get("/api/cases")
async def cases() -> dict[str, object]:
    experiment_id, top_k, frozen_cases = load_cases()
    return {
        "experiment_id": experiment_id,
        "top_k": top_k,
        "cases": [case.model_dump(mode="json") for case in frozen_cases],
    }


def _saved_evaluation_path() -> Path:
    root = repository_root()
    # The experiment report pins this artifact. Fixture evaluations may update
    # results/latest.json, but they must never replace the UI's experiment evidence.
    frozen_experiment = root / "results" / "runs" / "vertex-adk.json"
    if frozen_experiment.exists():
        return frozen_experiment
    return root / "results" / "latest.json"


def _saved_evaluation() -> dict[str, object] | None:
    path = _saved_evaluation_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_case(case_id: str) -> dict[str, object] | None:
    payload = _saved_evaluation()
    if payload is None:
        return None
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return None
    for result in cases:
        if isinstance(result, dict) and result.get("case_id") == case_id:
            return result
    return None


@app.get("/api/cases/{case_id}/result")
async def case_result(
    case_id: str,
    source: str = Query(default="fixture", pattern="^(fixture|latest)$"),
) -> dict[str, object]:
    _, top_k, frozen_cases = load_cases()
    case = next((item for item in frozen_cases if item.id == case_id), None)
    if case is None:
        raise HTTPException(status_code=404, detail="unknown frozen case")
    if source == "latest":
        saved_result = _latest_case(case_id)
        if saved_result is None:
            raise HTTPException(status_code=404, detail="no saved evaluation result for case")
        return {"result_source": "saved-evaluation", "result": saved_result}

    retriever = HybridRetriever(load_artifacts(), build_embedder("local"))
    provider = FixtureProvider(inject_unsupported=True)
    fixture_result = await run_case(case, retriever, provider, top_k)
    return {
        "result_source": "deterministic-fixture-not-llm-evidence",
        "result": fixture_result.model_dump(mode="json"),
    }


@app.get("/api/evaluation")
async def latest_evaluation() -> dict[str, object]:
    payload = _saved_evaluation()
    if payload is None:
        raise HTTPException(status_code=404, detail="no saved evaluation result")
    return payload


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
