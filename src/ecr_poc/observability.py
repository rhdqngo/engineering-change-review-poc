from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

SAFE_FIELDS = {
    "run_id",
    "case_id",
    "role",
    "model",
    "candidate_fingerprint",
    "verified",
    "blocked",
    "blocked_stage",
    "latency_ms",
    "error_type",
    "failure_write_error_type",
    "cases",
    "completed_cases",
}


def log_event(event: str, *, severity: str = "INFO", **fields: Any) -> None:
    unsafe = set(fields) - SAFE_FIELDS
    if unsafe:
        raise ValueError(f"Structured log contains non-allowlisted fields: {sorted(unsafe)}")
    payload = {
        "severity": severity,
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        **{key: value for key, value in fields.items() if value is not None},
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()
