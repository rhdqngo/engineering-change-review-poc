import pytest

from ecr_poc.observability import log_event


def test_structured_logging_rejects_raw_content_fields() -> None:
    with pytest.raises(ValueError, match="non-allowlisted"):
        log_event("role_completed", run_id="run", evidence="raw source text")


def test_decision_log_schema_allows_only_safe_decision_metadata(capsys) -> None:
    log_event(
        "decision_recorded",
        run_id="run",
        case_id="DIR-01",
        role="evidence_verifier",
        source_id="CONFIG_FUNCTION_CODES",
        decision="VERIFIED_REVIEW",
        verifier_verdict="SUPPORTED",
    )
    output = capsys.readouterr().out
    assert '"source_id":"CONFIG_FUNCTION_CODES"' in output
    assert '"decision":"VERIFIED_REVIEW"' in output
    assert '"evidence":' not in output
