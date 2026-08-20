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


def load_experiment_manifest(
    root: Path | None = None, name: str = "ecr-poc-v2.json"
) -> dict[str, Any]:
    root = root or repository_root()
    return _load_json(root / "data" / "experiments" / name)


def validate_experiment_manifest(
    root: Path | None = None, name: str = "ecr-poc-v2.json"
) -> dict[str, str]:
    root = root or repository_root()
    manifest = load_experiment_manifest(root, name)
    if manifest.get("experiment_id") != "ecr-poc-preregistered-v2":
        raise DataIntegrityError("Unexpected v2 experiment ID")
    if manifest.get("results_observed_before_freeze") is not False:
        raise DataIntegrityError("v2 manifest must be frozen before observing v2 results")
    _, top_k, cases = load_cases(root)
    if int(manifest.get("top_k", -1)) != top_k:
        raise DataIntegrityError("v2 manifest Top-K does not match frozen cases")
    expected_counts = manifest.get("case_counts")
    actual_counts: dict[str, int] = {}
    for case in cases:
        actual_counts[case.type] = actual_counts.get(case.type, 0) + 1
    if expected_counts != actual_counts:
        raise DataIntegrityError("v2 manifest case distribution changed")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise DataIntegrityError("v2 manifest is missing frozen files")
    validated: dict[str, str] = {}
    for relative, expected_hash in files.items():
        path = root / str(relative)
        if not path.is_file():
            raise DataIntegrityError(f"v2 frozen file is missing: {relative}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise DataIntegrityError(
                f"v2 frozen file hash mismatch for {relative}: {actual_hash} != {expected_hash}"
            )
        validated[str(relative)] = actual_hash
    prompt_file = manifest.get("prompt_file")
    prompt_hashes = manifest.get("prompt_hashes")
    if not isinstance(prompt_file, str) or not isinstance(prompt_hashes, dict):
        raise DataIntegrityError("v2 manifest is missing role prompt hashes")
    prompt_document = _load_json(root / prompt_file)
    if prompt_document.get("version") != manifest.get("prompt_version"):
        raise DataIntegrityError("v2 prompt version changed")
    expected_roles = {"change_analyst", "engineering_review", "evidence_verifier"}
    if set(prompt_hashes) != expected_roles:
        raise DataIntegrityError("v2 role prompt hash set changed")
    for role in expected_roles:
        instruction = prompt_document.get(role)
        if not isinstance(instruction, str) or not instruction:
            raise DataIntegrityError(f"v2 prompt instruction is missing: {role}")
        actual_hash = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
        if actual_hash != prompt_hashes[role]:
            raise DataIntegrityError(f"v2 role prompt hash mismatch for {role}")
    return validated


def validate_all(root: Path | None = None) -> dict[str, int]:
    root = root or repository_root()
    validate_freeze(root)
    validate_provenance(root)
    artifacts = load_artifacts(root)
    _, _, cases = load_cases(root)
    validate_expected_evidence(cases, artifacts)
    validate_experiment_manifest(root)
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
