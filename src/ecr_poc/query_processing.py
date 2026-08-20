from __future__ import annotations

import hashlib
import json
import re

from .models import IncomingArtifact, QueryProcessingResult

PROCESSOR_VERSION = "incoming-query-v2-deterministic"
_TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,119}\b")
_CAMEL = re.compile(r"[a-z0-9][A-Z]")


def _is_code_like(value: str) -> bool:
    return (
        "_" in value
        or _CAMEL.search(value) is not None
        or (any(char.isdigit() for char in value) and any(char.isalpha() for char in value))
    )


def extract_query_identifiers(incoming: IncomingArtifact) -> list[str]:
    ordered = list(incoming.identifiers)
    raw = "\n".join(
        value
        for value in (incoming.title, incoming.subsystem, incoming.text)
        if value
    )
    ordered.extend(token for token in _TOKEN.findall(raw) if _is_code_like(token))
    return list(dict.fromkeys(ordered))


def process_query(incoming: IncomingArtifact) -> QueryProcessingResult:
    identifiers = extract_query_identifiers(incoming)
    fields = [
        incoming.artifact_type.value,
        incoming.title or "",
        incoming.subsystem or "",
        "\n".join(incoming.identifiers),
        incoming.text,
        "\n".join(
            identifier
            for identifier in identifiers
            if identifier not in incoming.identifiers
        ),
    ]
    query_text = "\n".join(fields)
    identity = {
        "processor_version": PROCESSOR_VERSION,
        "query_text": query_text,
        "extracted_identifiers": identifiers,
    }
    fingerprint = hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return QueryProcessingResult(
        processor_version=PROCESSOR_VERSION,
        extracted_identifiers=identifiers,
        query_fingerprint=fingerprint,
        query_text=query_text,
    )
