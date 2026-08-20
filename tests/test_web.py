from fastapi.testclient import TestClient

from ecr_poc.web import app

client = TestClient(app)


def test_health_and_case_catalog() -> None:
    assert client.get("/health").json() == {
        "status": "ok",
        "data_freeze": "valid",
    }
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
    assert payload["result_source"] == "saved-evaluation"
    assert payload["result"]["case_id"] == "SEM-01"
    assert payload["result"]["provider"] == "vertex-adk"

    evaluation = client.get("/api/evaluation")
    assert evaluation.status_code == 200
    assert evaluation.json()["provider"] == "vertex-adk"
