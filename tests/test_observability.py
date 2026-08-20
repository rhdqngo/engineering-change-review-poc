import pytest

from ecr_poc.observability import log_event


def test_structured_logging_rejects_raw_content_fields() -> None:
    with pytest.raises(ValueError, match="non-allowlisted"):
        log_event("role_completed", run_id="run", evidence="raw source text")
