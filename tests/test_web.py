from pathlib import Path

from fastapi.testclient import TestClient

from ecr_poc import web
from ecr_poc.providers import FixtureProvider
from ecr_poc.web import app

client = TestClient(app)


def test_health_and_case_catalog() -> None:
    health = client.get("/health").json()
    assert health == {"status": "alive"}
    readiness = client.get("/readyz").json()
    assert readiness["status"] == "ready"
    assert readiness["data_integrity"] == "valid"
    assert readiness["result_store"] == "local"
    assert readiness["published_run_id"] == "fixture-v6-purpose-driven"
    assert readiness["freeze_version"] == "ecr-poc-regression-v6"
    assert readiness["embedding_index_fingerprint"]
    assert readiness["identifier_index_fingerprint"]
    integrity = client.get("/integrity").json()
    assert integrity["active_experiment_id"] == "ecr-poc-regression-v6"
    assert integrity["published_cases"] == 20
    payload = client.get("/api/cases").json()
    assert payload["experiment_id"] == "ecr-poc-regression-v6"
    assert payload["top_k"] == 10
    assert len(payload["cases"]) == 20
    assert payload["cases"][0]["incoming_artifact"]["text"]


def test_fixture_case_and_unknown_case_paths() -> None:
    response = client.get("/api/cases/DIR-01/result?source=fixture")
    assert response.status_code == 200
    payload = response.json()
    assert payload["result_source"] == "deterministic-fixture-not-llm-evidence"
    assert payload["result"]["baseline_candidate_source_ids"] == payload["result"][
        "proposed_candidate_source_ids"
    ]
    assert client.get("/api/cases/UNKNOWN/result").status_code == 404


def test_saved_evaluation_case_path() -> None:
    response = client.get("/api/cases/SEM-01/result?source=latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["result_source"] == "published-evaluation"
    assert payload["result_metadata"]["result_store"] == "local"
    assert payload["result"]["case_id"] == "SEM-01"
    assert payload["result"]["provider"] == "fixture-not-llm"

    evaluation = client.get("/api/evaluation")
    assert evaluation.status_code == 200
    assert evaluation.json()["experiment_id"] == "ecr-poc-regression-v6"


def test_published_alias_and_gcs_failure_are_fail_closed(monkeypatch) -> None:
    published = client.get("/api/cases/SEM-01/result?source=published")
    assert published.status_code == 200
    assert published.json()["result_source"] == "published-evaluation"

    monkeypatch.setenv("ECR_RESULT_STORE", "gcs")
    monkeypatch.setenv("ECR_GCS_BUCKET", "test-bucket")

    def unavailable(_bucket, _published_object):
        raise PermissionError("simulated GCS denial")

    monkeypatch.setattr(web, "load_published_run", unavailable)
    response = client.get("/api/evaluation")
    assert response.status_code == 503
    assert "simulated GCS denial" in response.json()["detail"]
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503
    assert client.get("/integrity").status_code == 503


def test_published_evaluation_uses_short_ttl_cache(monkeypatch) -> None:
    monkeypatch.setenv("ECR_PUBLISHED_CACHE_TTL_SECONDS", "30")
    monkeypatch.setattr(web, "_PUBLISHED_CACHE", None)
    calls = 0

    def load_once():
        nonlocal calls
        calls += 1
        return (
            {"experiment_id": "ecr-poc-regression-v6", "cases": []},
            {"freeze_version": "ecr-poc-regression-v6"},
        )

    monkeypatch.setattr(web, "_load_published_evaluation_uncached", load_once)
    web._published_evaluation_sync()
    web._published_evaluation_sync()
    assert calls == 1


def test_live_and_evaluation_ui_preserve_contract_and_accessible_selection() -> None:
    static_root = Path(__file__).parents[1] / "src" / "ecr_poc" / "static"
    script = (static_root / "evaluation.js").read_text(encoding="utf-8")
    live_script = (static_root / "live.js").read_text(encoding="utf-8")
    markup = (static_root / "index.html").read_text(encoding="utf-8")
    evaluation_markup = (static_root / "evaluation.html").read_text(encoding="utf-8")
    styles = (static_root / "styles.css").read_text(encoding="utf-8")

    assert 'state.resultMetadata?.freeze_version' in script
    assert 'compactRunId(publishedRunId)' in script
    assert 'publishedRunId || "unknown"' in script
    assert 'Frozen regression benchmark' in script
    assert 'setAttribute("aria-pressed"' in script
    assert 'setAttribute("aria-controls", "evidence-desk")' in script
    assert '<button id="run-button" type="button" disabled>Reload result</button>' in evaluation_markup
    assert 'Loading review disposition…' in evaluation_markup
    assert 'state.resultController?.abort()' in script
    assert 'requestSequence !== state.requestSequence' in script
    assert 'if (restoreReloadFocus) runButton.focus()' in script
    assert 'item.incoming_artifact' in script
    assert 'result.provenance?.identifier_index_fingerprint' in script
    assert 'clearResultSurface(source === "published"' in script
    assert 'runButton.textContent = "Retry catalog"' in script
    assert 'jsonResponse(await fetch("/api/cases"' in script
    assert 'response was not valid JSON' in script
    assert 'scroll.scrollBy({ left: event.key === "ArrowRight" ? 160 : -160 })' in script
    assert 'class="table-wrap" tabindex="0" role="region"' in evaluation_markup
    assert 'id="blocked-records"' in evaluation_markup
    assert 'broad_candidate_fingerprint' in script
    assert 'expanded_pool_fingerprint' in script
    assert '.table-wrap:focus-visible' in styles
    assert '.blocked-record-button' in styles
    assert '#run-button { min-width: 126px; white-space: nowrap; }' in styles
    assert 'id="evidence-desk"' in markup
    assert 'aria-live="polite"' in markup
    assert 'Run engineering review · uses Vertex AI' in markup
    assert 'localStorage' not in live_script
    assert 'resultSummary.focus()' in live_script
    assert 'NO_SUPPORTED_REVIEW' in live_script
    assert 'result.final_docket' in live_script
    assert 'candidate_results' in live_script
    assert 'verified_claims' in live_script
    assert 'Broad' in markup and 'Expanded' in markup and 'Final' in markup
    assert 'preregistered' not in evaluation_markup.lower()
    assert '.source-button { width: 100%; padding: 4px 0; min-height: 38px;' in styles
    assert 'tbody tr { cursor: pointer; }' not in styles
    assert '.change-delta { grid-template-columns: 1fr; }' in styles


def test_live_review_contract_validation_and_concurrency(monkeypatch) -> None:
    valid = {
        "incoming_artifact": {
            "artifact_type": "requirement",
            "text": "SAMPLE_APP shall use a command pipe depth of 32 messages.",
            "identifiers": ["SAMPLE_APP_CMD_PIPE_DEPTH"],
        }
    }
    response = client.post("/api/reviews", json=valid)
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] in {
        "REVIEW_REQUIRED", "NO_SUPPORTED_REVIEW", "INCONCLUSIVE"
    }
    assert len(payload["final_docket"]) == 10
    assert payload["retrieval"]["broad_count"] == 40
    assert payload["retrieval"]["expanded_count"] <= 200
    assert payload["retrieval"]["final_docket_fingerprint"]
    assert payload["identifier_index_fingerprint"]
    assert "incoming_artifact" not in payload
    assert valid["incoming_artifact"]["text"] not in response.text
    assert payload["retention"] == "not_saved"
    assert payload["embedding_index_fingerprint"]
    runtime = web._live_runtime()
    monkeypatch.setattr(
        web,
        "_LIVE_RUNTIME",
        web.LiveRuntime(
            runtime.baseline_id,
            runtime.top_k,
            runtime.retriever,
            FixtureProvider(live_outcome="review"),
        ),
    )
    assert client.post("/api/reviews", json=valid).json()["overall_status"] == "REVIEW_REQUIRED"
    monkeypatch.setattr(
        web,
        "_LIVE_RUNTIME",
        web.LiveRuntime(
            runtime.baseline_id,
            runtime.top_k,
            runtime.retriever,
            FixtureProvider(live_outcome="inconclusive"),
        ),
    )
    assert client.post("/api/reviews", json=valid).json()["overall_status"] == "INCONCLUSIVE"
    assert client.post(
        "/api/reviews",
        json={"incoming_artifact": {"artifact_type": "requirement", "text": " "}},
    ).status_code == 422
    assert client.post(
        "/api/reviews",
        json={"incoming_artifact": {"artifact_type": "requirement", "text": "x" * 20001}},
    ).status_code == 422
    assert web._LIVE_EXECUTION_LOCK.acquire(blocking=False)
    try:
        assert client.post("/api/reviews", json=valid).status_code == 429
    finally:
        web._LIVE_EXECUTION_LOCK.release()
