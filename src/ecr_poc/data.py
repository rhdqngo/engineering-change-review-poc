from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .models import ArtifactSpan, CaseDefinition


class DataIntegrityError(RuntimeError):
    pass


DEFAULT_EXPERIMENT_MANIFEST = "ecr-poc-v5.json"
ACTIVE_CASE_FILE = "cases-v5.json"
ACTIVE_EXPERIMENT_ID = "ecr-poc-preregistered-v5"
HISTORICAL_EXPERIMENT_MANIFESTS = (
    "ecr-poc-v2.json",
    "ecr-poc-v3.json",
    "ecr-poc-v4.json",
)
SUPPORTED_EXPERIMENT_MANIFESTS = (*HISTORICAL_EXPERIMENT_MANIFESTS, DEFAULT_EXPERIMENT_MANIFEST)


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


def _upgrade_legacy_case(record: dict[str, Any]) -> dict[str, Any]:
    upgraded = dict(record)
    expected_targets = [str(value) for value in record.get("expected_review_targets", [])]
    legacy_evidence = record.get("expected_evidence")
    expected_evidence_by_target: list[dict[str, Any]] = []
    if isinstance(legacy_evidence, dict):
        expected_evidence_by_target.append(
            {
                "source_id": str(legacy_evidence["source_id"]),
                "spans": [str(legacy_evidence["span"])],
            }
        )
    change: dict[str, Any] = (
        record["change"] if isinstance(record.get("change"), dict) else {}
    )
    changed_source_id = (
        str(legacy_evidence["source_id"])
        if isinstance(legacy_evidence, dict)
        else expected_targets[0]
        if expected_targets
        else "CTX_README"
    )
    old_value = change.get("old_value")
    new_value = change.get("new_value")
    upgraded.pop("expected_evidence", None)
    upgraded.update(
        {
            "changed_source_id": changed_source_id,
            "original_content": str(old_value if old_value is not None else record["change_text"]),
            "changed_content": str(new_value if new_value is not None else record["change_text"]),
            "expected_evidence_by_target": expected_evidence_by_target,
        }
    )
    return upgraded


def load_cases(
    root: Path | None = None,
    experiment_manifest: str | None = None,
) -> tuple[str, int, list[CaseDefinition]]:
    root = root or repository_root()
    case_file = ACTIVE_CASE_FILE
    if experiment_manifest is not None:
        manifest = load_experiment_manifest(root, experiment_manifest)
        case_file = str(manifest.get("case_file", "data/cases/cases.json"))
        if Path(case_file).name != case_file:
            case_path = root / case_file
        else:
            case_path = root / "data" / "cases" / case_file
    else:
        case_path = root / "data" / "cases" / case_file
    document = _load_json(case_path)
    records = document.get("cases")
    if not isinstance(records, list):
        raise DataIntegrityError("cases.json is missing its cases array")
    schema_version = int(document.get("schema_version", 1))
    cases = [
        CaseDefinition.model_validate(
            record if schema_version >= 2 else _upgrade_legacy_case(record)
        )
        for record in records
        if isinstance(record, dict)
    ]
    case_ids = [case.id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise DataIntegrityError("Duplicate case ID")
    return str(document["experiment_id"]), int(document["top_k"]), cases


def validate_expected_evidence(
    cases: list[CaseDefinition], artifacts: list[ArtifactSpan]
) -> None:
    by_id = {artifact.source_id: artifact for artifact in artifacts}
    for case in cases:
        changed_artifact = by_id.get(case.changed_source_id)
        if changed_artifact is None:
            raise DataIntegrityError(
                f"{case.id} has unknown changed source {case.changed_source_id}"
            )
        if case.type != "clean" and case.original_content not in changed_artifact.content:
            raise DataIntegrityError(
                f"{case.id} original content is not an exact changed-source span"
            )
        for target in case.expected_review_targets:
            if target not in by_id:
                raise DataIntegrityError(f"{case.id} has unknown expected target {target}")
        evidence_sources = [item.source_id for item in case.expected_evidence_by_target]
        if len(evidence_sources) != len(set(evidence_sources)):
            raise DataIntegrityError(f"{case.id} has duplicate target evidence entries")
        if set(evidence_sources) != set(case.expected_review_targets):
            raise DataIntegrityError(
                f"{case.id} target evidence does not match expected review targets"
            )
        for expected in case.expected_evidence_by_target:
            artifact = by_id.get(expected.source_id)
            if artifact is None:
                raise DataIntegrityError(
                    f"{case.id} has unknown evidence source {expected.source_id}"
                )
            for span in expected.spans:
                if span not in artifact.content:
                    raise DataIntegrityError(
                        f"{case.id} expected evidence is not an exact source span"
                    )


def load_experiment_manifest(
    root: Path | None = None, name: str = DEFAULT_EXPERIMENT_MANIFEST
) -> dict[str, Any]:
    root = root or repository_root()
    if Path(name).name != name:
        raise DataIntegrityError(f"Unsafe experiment manifest name: {name}")
    return _load_json(root / "data" / "experiments" / name)


def experiment_manifest_name(experiment_id: str) -> str:
    match = re.fullmatch(
        r"ecr-poc-preregistered-(v[2-9][0-9]*(?:-[a-z][a-z0-9-]*)?)",
        experiment_id,
    )
    if match is None:
        raise DataIntegrityError(f"Unsupported cloud experiment ID: {experiment_id}")
    return f"ecr-poc-{match.group(1)}.json"


def validate_experiment_manifest(
    root: Path | None = None, name: str = DEFAULT_EXPERIMENT_MANIFEST
) -> dict[str, str]:
    root = root or repository_root()
    manifest = load_experiment_manifest(root, name)
    version_match = re.fullmatch(
        r"ecr-poc-(v([2-9][0-9]*)(?:-[a-z][a-z0-9-]*)?)\.json",
        name,
    )
    if version_match is None:
        raise DataIntegrityError(f"Unsupported experiment manifest name: {name}")
    version_key = version_match.group(1)
    version = version_match.group(2)
    expected_experiment_id = f"ecr-poc-preregistered-{version_key}"
    if manifest.get("experiment_id") != expected_experiment_id:
        raise DataIntegrityError(f"Unexpected {version_key} experiment ID")
    if manifest.get("freeze_tag") != f"ecr-poc-{version_key}-freeze":
        raise DataIntegrityError(f"Unexpected {version_key} freeze tag")
    if manifest.get("results_observed_before_freeze") is not False:
        raise DataIntegrityError(
            f"v{version} manifest must be frozen before observing v{version} results"
        )
    _, top_k, cases = load_cases(root, name)
    if int(manifest.get("top_k", -1)) != top_k:
        raise DataIntegrityError(
            f"v{version} manifest Top-K does not match frozen cases"
        )
    expected_counts = manifest.get("case_counts")
    actual_counts: dict[str, int] = {}
    for case in cases:
        actual_counts[case.type] = actual_counts.get(case.type, 0) + 1
    if expected_counts != actual_counts:
        raise DataIntegrityError(f"v{version} manifest case distribution changed")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise DataIntegrityError(f"v{version} manifest is missing frozen files")
    validated: dict[str, str] = {}
    for relative, expected_hash in files.items():
        path = root / str(relative)
        if not path.is_file():
            raise DataIntegrityError(f"v{version} frozen file is missing: {relative}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise DataIntegrityError(
                f"v{version} frozen file hash mismatch for {relative}: "
                f"{actual_hash} != {expected_hash}"
            )
        validated[str(relative)] = actual_hash
    prompt_file = manifest.get("prompt_file")
    prompt_hashes = manifest.get("prompt_hashes")
    if not isinstance(prompt_file, str) or not isinstance(prompt_hashes, dict):
        raise DataIntegrityError(
            f"v{version} manifest is missing role prompt hashes"
        )
    prompt_document = _load_json(root / prompt_file)
    if prompt_document.get("version") != manifest.get("prompt_version"):
        raise DataIntegrityError(f"v{version} prompt version changed")
    expected_roles = {"change_analyst", "engineering_review", "evidence_verifier"}
    if set(prompt_hashes) != expected_roles:
        raise DataIntegrityError(f"v{version} role prompt hash set changed")
    for role in expected_roles:
        instruction = prompt_document.get(role)
        if not isinstance(instruction, str) or not instruction:
            raise DataIntegrityError(
                f"v{version} prompt instruction is missing: {role}"
            )
        actual_hash = hashlib.sha256(instruction.encode("utf-8")).hexdigest()
        if actual_hash != prompt_hashes[role]:
            raise DataIntegrityError(
                f"v{version} role prompt hash mismatch for {role}"
            )
    if int(version) >= 5:
        embedding_index_file = manifest.get("embedding_index_file")
        if not isinstance(embedding_index_file, str):
            raise DataIntegrityError("v5 manifest is missing its embedding index file")
        embedding_index = _load_json(root / embedding_index_file)
        allowed_embedding_experiments = {
            expected_experiment_id,
            str(manifest.get("base_experiment_id", "")),
        }
        if embedding_index.get("experiment_id") not in allowed_embedding_experiments:
            raise DataIntegrityError("v5 embedding index experiment ID mismatch")
        if embedding_index.get("embedding_model") != manifest["retrieval"]["embedding_model"]:
            raise DataIntegrityError("v5 embedding index model mismatch")
    return validated


def validate_all(root: Path | None = None) -> dict[str, int]:
    root = root or repository_root()
    validate_provenance(root)
    artifacts = load_artifacts(root)
    _, _, cases = load_cases(root)
    validate_expected_evidence(cases, artifacts)
    validate_experiment_manifest(root, DEFAULT_EXPERIMENT_MANIFEST)
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


def validate_historical_versions(root: Path | None = None) -> dict[str, object]:
    root = root or repository_root()
    freeze_hashes = validate_freeze(root)
    manifests = {
        name: validate_experiment_manifest(root, name)
        for name in HISTORICAL_EXPERIMENT_MANIFESTS
    }
    return {
        "freeze_files": len(freeze_hashes),
        "manifests": list(manifests),
    }
