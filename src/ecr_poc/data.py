from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import ArtifactSpan, CaseDefinition


class DataIntegrityError(RuntimeError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise DataIntegrityError(f"Expected a JSON object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_freeze(root: Path | None = None) -> dict[str, str]:
    root = root or repository_root()
    freeze = _load_json(root / "data" / "cases" / "freeze.json")
    expected_files = freeze.get("files")
    if not isinstance(expected_files, dict):
        raise DataIntegrityError("freeze.json is missing its files object")
    validated: dict[str, str] = {}
    for relative, expected_hash in expected_files.items():
        path = root / relative
        if not path.is_file():
            raise DataIntegrityError(f"Frozen file is missing: {relative}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise DataIntegrityError(
                f"Frozen file hash mismatch for {relative}: {actual_hash} != {expected_hash}"
            )
        validated[str(relative)] = actual_hash
    return validated


def validate_provenance(root: Path | None = None) -> None:
    root = root or repository_root()
    provenance = _load_json(root / "data" / "nasa" / "provenance.json")
    source_root = root / str(provenance["source_root"])
    files = provenance.get("files")
    if not isinstance(files, list):
        raise DataIntegrityError("provenance.json is missing its files array")
    for item in files:
        if not isinstance(item, dict):
            raise DataIntegrityError("Invalid provenance item")
        relative = str(item["path"])
        path = source_root / relative
        if not path.is_file():
            raise DataIntegrityError(f"Pinned NASA source is missing: {relative}")
        actual_hash = sha256_file(path)
        expected_hash = str(item["sha256"])
        if actual_hash != expected_hash:
            raise DataIntegrityError(
                f"Pinned NASA source hash mismatch for {relative}: {actual_hash} != {expected_hash}"
            )
        if path.stat().st_size != int(item["bytes"]):
            raise DataIntegrityError(f"Pinned NASA source byte count mismatch: {relative}")


def load_artifacts(root: Path | None = None) -> list[ArtifactSpan]:
    root = root or repository_root()
    manifest = _load_json(root / "data" / "nasa" / "artifacts.json")
    source_root = root / str(manifest["source_root"])
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        raise DataIntegrityError("artifacts.json is missing its artifacts array")
    artifacts: list[ArtifactSpan] = []
    source_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise DataIntegrityError("Invalid artifact record")
        source_id = str(record["source_id"])
        if source_id in source_ids:
            raise DataIntegrityError(f"Duplicate source ID: {source_id}")
        source_ids.add(source_id)
        path = source_root / str(record["path"])
        lines = path.read_text(encoding="utf-8").splitlines()
        start = int(record["start_line"])
        end = int(record["end_line"])
        if start < 1 or end < start or end > len(lines):
            raise DataIntegrityError(
                f"Invalid line range for {source_id}: {start}-{end} in {len(lines)} lines"
            )
        content = "\n".join(lines[start - 1 : end])
        artifacts.append(ArtifactSpan(content=content, **record))
    return artifacts


def load_cases(root: Path | None = None) -> tuple[str, int, list[CaseDefinition]]:
    root = root or repository_root()
    document = _load_json(root / "data" / "cases" / "cases.json")
    records = document.get("cases")
    if not isinstance(records, list):
        raise DataIntegrityError("cases.json is missing its cases array")
    cases = [CaseDefinition.model_validate(record) for record in records]
    case_ids = [case.id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise DataIntegrityError("Duplicate case ID")
    return str(document["experiment_id"]), int(document["top_k"]), cases


def validate_expected_evidence(
    cases: list[CaseDefinition], artifacts: list[ArtifactSpan]
) -> None:
    by_id = {artifact.source_id: artifact for artifact in artifacts}
    for case in cases:
        for target in case.expected_review_targets:
            if target not in by_id:
                raise DataIntegrityError(f"{case.id} has unknown expected target {target}")
        if case.expected_evidence is None:
            continue
        artifact = by_id.get(case.expected_evidence.source_id)
        if artifact is None:
            raise DataIntegrityError(
                f"{case.id} has unknown evidence source {case.expected_evidence.source_id}"
            )
        if case.expected_evidence.span not in artifact.content:
            raise DataIntegrityError(f"{case.id} expected evidence is not an exact source span")


def validate_all(root: Path | None = None) -> dict[str, int]:
    root = root or repository_root()
    validate_freeze(root)
    validate_provenance(root)
    artifacts = load_artifacts(root)
    _, _, cases = load_cases(root)
    validate_expected_evidence(cases, artifacts)
    type_counts: dict[str, int] = {}
    for case in cases:
        type_counts[case.type] = type_counts.get(case.type, 0) + 1
    expected = {
        "direct": 4,
        "semantic": 4,
        "cross_artifact": 4,
        "clean": 3,
        "benign": 3,
    }
    if type_counts != expected:
        raise DataIntegrityError(f"Case distribution changed: {type_counts} != {expected}")
    return {"artifacts": len(artifacts), "cases": len(cases), **type_counts}
