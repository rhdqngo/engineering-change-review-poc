from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ArtifactSpan

SCHEMA_VERSION = 1
EXTRACTOR_VERSION = "engineering-identifier-index-v1"
MIN_EXPANSION_DF = 2
MAX_EXPANSION_DF = 50
MAX_IDENTIFIERS_PER_SEED = 8

_TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,119}\b")
_CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,119})\s*\(")
_XML_NAME = re.compile(r"\b(?:name|id|type)=[\"']([A-Za-z_][A-Za-z0-9_.:-]{2,119})[\"']")
_KEYWORDS = {
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "inline",
    "int",
    "long",
    "register",
    "restrict",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while",
}
_GENERIC = {
    "NULL",
    "TRUE",
    "FALSE",
    "SUCCESS",
    "ERROR",
    "size_t",
    "int8_t",
    "int16_t",
    "int32_t",
    "int64_t",
    "uint8_t",
    "uint16_t",
    "uint32_t",
    "uint64_t",
}


@dataclass(frozen=True)
class IdentifierEntry:
    identifier: str
    kind: str
    scope: str
    document_frequency: int
    postings: tuple[str, ...]


class IdentifierIndex:
    def __init__(
        self,
        entries: list[IdentifierEntry],
        *,
        artifact_package_sha256: str,
        fingerprint: str,
        object_sha256: str | None = None,
    ) -> None:
        self.entries = entries
        self.artifact_package_sha256 = artifact_package_sha256
        self.fingerprint = fingerprint
        self.object_sha256 = object_sha256
        self._by_identifier: dict[str, list[IdentifierEntry]] = defaultdict(list)
        self._by_source: dict[str, list[IdentifierEntry]] = defaultdict(list)
        for entry in entries:
            self._by_identifier[entry.identifier].append(entry)
            for source_id in entry.postings:
                self._by_source[source_id].append(entry)

    def eligible_entries(self, identifier: str) -> list[IdentifierEntry]:
        return [
            entry
            for entry in self._by_identifier.get(identifier, [])
            if MIN_EXPANSION_DF <= entry.document_frequency <= MAX_EXPANSION_DF
        ]

    def seed_identifiers(self, source_id: str, corpus_size: int) -> list[str]:
        eligible = [
            entry
            for entry in self._by_source.get(source_id, [])
            if MIN_EXPANSION_DF <= entry.document_frequency <= MAX_EXPANSION_DF
        ]
        eligible.sort(
            key=lambda entry: (
                -identifier_specificity(entry.document_frequency, corpus_size),
                entry.identifier,
                entry.kind,
            )
        )
        return list(dict.fromkeys(entry.identifier for entry in eligible))[
            :MAX_IDENTIFIERS_PER_SEED
        ]


def _kind(identifier: str, artifact: ArtifactSpan, calls: set[str]) -> str | None:
    if identifier in _KEYWORDS or identifier in _GENERIC:
        return None
    upper = identifier.upper()
    if upper.endswith("_MID"):
        return "message_id"
    if upper.endswith("_CC"):
        return "command_code"
    if "TBL" in upper or "TABLE" in upper:
        return "table"
    if identifier.endswith("_t"):
        return "type"
    if identifier in calls:
        return "function"
    if "_" in identifier and identifier == upper and any(char.isalpha() for char in identifier):
        return "macro"
    if artifact.type in {"interface", "configuration"} and "_" in identifier:
        return "symbol"
    if artifact.type == "verification" and identifier.startswith(
        ("Test_", "Test", "UtAssert")
    ):
        return "test_target"
    return None


def extract_artifact_identifiers(artifact: ArtifactSpan) -> set[tuple[str, str, str]]:
    calls = set(_CALL.findall(artifact.content))
    values: set[tuple[str, str, str]] = set()
    for identifier in _TOKEN.findall(artifact.content):
        kind = _kind(identifier, artifact, calls)
        if kind is not None:
            values.add((identifier, kind, "global"))
    if artifact.symbol and _TOKEN.fullmatch(artifact.symbol):
        kind = _kind(artifact.symbol, artifact, calls) or "symbol"
        if artifact.symbol not in _KEYWORDS and artifact.symbol not in _GENERIC:
            values.add((artifact.symbol, kind, "global"))
    for identifier in _XML_NAME.findall(artifact.content):
        values.add((identifier, "eds_xml", "global"))
    return values


def _canonical_identity(
    entries: list[dict[str, Any]], artifact_package_sha256: str
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "artifact_package_sha256": artifact_package_sha256,
        "entries": entries,
    }


def build_identifier_index_document(
    artifacts: list[ArtifactSpan], artifact_package_sha256: str
) -> dict[str, Any]:
    postings: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for artifact in artifacts:
        for key in extract_artifact_identifiers(artifact):
            postings[key].add(artifact.source_id)
    entries = [
        {
            "identifier": identifier,
            "kind": kind,
            "scope": scope,
            "document_frequency": len(source_ids),
            "postings": sorted(source_ids),
        }
        for (identifier, kind, scope), source_ids in sorted(postings.items())
    ]
    identity = _canonical_identity(entries, artifact_package_sha256)
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**identity, "fingerprint": fingerprint}


def build_identifier_index(
    artifacts: list[ArtifactSpan], artifact_package_sha256: str = "in-memory"
) -> IdentifierIndex:
    document = build_identifier_index_document(artifacts, artifact_package_sha256)
    entries = [
        IdentifierEntry(
            identifier=str(record["identifier"]),
            kind=str(record["kind"]),
            scope=str(record["scope"]),
            document_frequency=int(record["document_frequency"]),
            postings=tuple(str(value) for value in record["postings"]),
        )
        for record in document["entries"]
    ]
    return IdentifierIndex(
        entries,
        artifact_package_sha256=artifact_package_sha256,
        fingerprint=str(document["fingerprint"]),
    )


def write_identifier_index(
    path: Path, artifacts: list[ArtifactSpan], artifact_package_sha256: str
) -> dict[str, Any]:
    document = build_identifier_index_document(artifacts, artifact_package_sha256)
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "fingerprint": document["fingerprint"],
        "entries": len(document["entries"]),
    }


def load_identifier_index(
    path: Path,
    artifacts: list[ArtifactSpan],
    *,
    expected_artifact_package_sha256: str,
    expected_sha256: str | None = None,
) -> IdentifierIndex:
    payload = path.read_bytes()
    object_sha = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and object_sha != expected_sha256:
        raise ValueError("Identifier index object SHA-256 mismatch")
    document = json.loads(gzip.decompress(payload))
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Identifier index schema version mismatch")
    if document.get("extractor_version") != EXTRACTOR_VERSION:
        raise ValueError("Identifier index extractor version mismatch")
    if document.get("artifact_package_sha256") != expected_artifact_package_sha256:
        raise ValueError("Identifier index artifact package mismatch")
    records = document.get("entries")
    if not isinstance(records, list):
        raise TypeError("Identifier index entries are missing")
    source_ids = {artifact.source_id for artifact in artifacts}
    entries: list[IdentifierEntry] = []
    previous_key: tuple[str, str, str] | None = None
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("Identifier index entry is invalid")
        postings = tuple(str(value) for value in record.get("postings", []))
        if postings != tuple(sorted(set(postings))):
            raise ValueError("Identifier index postings are not unique and ordered")
        if not set(postings).issubset(source_ids):
            raise ValueError("Identifier index references an unknown source")
        key = (str(record["identifier"]), str(record["kind"]), str(record["scope"]))
        if previous_key is not None and key <= previous_key:
            raise ValueError("Identifier index entries are not uniquely ordered")
        previous_key = key
        if int(record["document_frequency"]) != len(postings):
            raise ValueError("Identifier index document frequency mismatch")
        entries.append(
            IdentifierEntry(
                identifier=key[0],
                kind=key[1],
                scope=key[2],
                document_frequency=len(postings),
                postings=postings,
            )
        )
    identity = _canonical_identity(records, expected_artifact_package_sha256)
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if document.get("fingerprint") != fingerprint:
        raise ValueError("Identifier index fingerprint mismatch")
    return IdentifierIndex(
        entries,
        artifact_package_sha256=expected_artifact_package_sha256,
        fingerprint=fingerprint,
        object_sha256=object_sha,
    )


def identifier_specificity(document_frequency: int, corpus_size: int) -> float:
    if document_frequency < MIN_EXPANSION_DF or corpus_size <= 1:
        return 0.0
    maximum = math.log((corpus_size + 1) / (MIN_EXPANSION_DF + 1))
    if maximum <= 0:
        return 0.0
    return max(
        0.0,
        min(1.0, math.log((corpus_size + 1) / (document_frequency + 1)) / maximum),
    )
