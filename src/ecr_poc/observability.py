from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from typing import Any

from .models import DecisionLogEvent


def log_event(event: str, *, severity: str = "INFO", **fields: Any) -> None:
    try:
        record = DecisionLogEvent(
            severity=severity,
            event=event,
            timestamp=datetime.now(UTC).isoformat(),
            **fields,
        )
    except ValueError as error:
        raise ValueError(f"Structured log contains non-allowlisted fields: {error}") from error
    payload = record.model_dump(mode="json", exclude_none=True)
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()
