from pathlib import Path

from fastapi.testclient import TestClient

from ecr_poc import web
from ecr_poc.web import app

client = TestClient(app)


def test_health_and_case_catalog() -> None:
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["data_freeze"] == "valid"
    assert health["result_store"] == "local"
    assert health["published_run_id"] == "c31aabbe-91a4-4a24-9d43-2515fe0d0155"
    assert health["freeze_version"] == "ecr-poc-preregistered-v1"
    payload = client.get("/api/cases").json()
    assert payload["top_k"] == 6
    assert len(payload["cases"]) == 18


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
    assert payload["result"]["provider"] == "vertex-adk"

    evaluation = client.get("/api/evaluation")
    assert evaluation.status_code == 200
    assert evaluation.json()["provider"] == "vertex-adk"


def test_published_alias_and_gcs_failure_are_fail_closed(monkeypatch) -> None:
    published = client.get("/api/cases/SEM-01/result?source=published")
    assert published.status_code == 200
    assert published.json()["result_source"] == "published-evaluation"

    monkeypatch.setenv("ECR_RESULT_STORE", "gcs")
    monkeypatch.setenv("ECR_GCS_BUCKET", "test-bucket")

    def unavailable(_bucket):
        raise PermissionError("simulated GCS denial")

    monkeypatch.setattr(web, "load_published_run", unavailable)
    response = client.get("/api/evaluation")
    assert response.status_code == 503
    assert "simulated GCS denial" in response.json()["detail"]
    assert client.get("/health").status_code == 503


def test_published_ui_preserves_provenance_and_accessible_selection() -> None:
    static_root = Path(__file__).parents[1] / "src" / "ecr_poc" / "static"
    script = (static_root / "app.js").read_text(encoding="utf-8")
    markup = (static_root / "index.html").read_text(encoding="utf-8")
    styles = (static_root / "styles.css").read_text(encoding="utf-8")

    assert 'state.resultMetadata?.freeze_version' in script
    assert 'compactRunId(publishedRunId)' in script
    assert 'publishedRunId || "unknown run"' in script
    assert '!isFixture && publishedRunId ? `Published run ${publishedRunId}`' in script
    assert 'replace(/^cloud-v\\d+-/, "")' in script
    assert 'setAttribute("aria-pressed"' in script
    assert 'setAttribute("aria-controls", "evidence-desk")' in script
    assert '<button id="run-button" type="button" disabled>Reload result</button>' in markup
    assert 'Loading review disposition…' in markup
    assert 'Run a case to inspect its review disposition.' not in markup
    assert 'id="evidence-desk"' in markup
    assert 'aria-live="polite"' in markup
    assert '.source-button { width: 100%; padding: 4px 0; min-height: 38px;' in styles
    assert 'tbody tr { cursor: pointer; }' not in styles
