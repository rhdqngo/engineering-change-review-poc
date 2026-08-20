from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ArtifactSpan

ALLOWED_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hh",
    ".hpp",
    ".xml",
    ".eds",
    ".md",
    ".dox",
    ".txt",
    ".cmake",
    ".mk",
    ".in",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".sh",
}
EXCLUDED_PARTS = {
    ".git",
    ".github",
    "actions",
    "build",
    "dist",
    "target",
    "generated",
    "vendor",
    "third_party",
    "node_modules",
    "__pycache__",
}
MAX_CHUNK_CHARS = 4_000
MAX_CHUNK_UTF8_BYTES = 1_800
FALLBACK_LINES = 80
FALLBACK_OVERLAP = 10
_SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]+")
_HEADING = re.compile(r"^\s*(?:#{1,6}\s+|\\(?:page|section|subsection)\s+)(.+)$")
_XML_NAMED = re.compile(r"^\s*<([A-Za-z_:][\w:.-]*)[^>]*(?:name|id)=['\"]([^'\"]+)['\"]")
_C_SYMBOL = re.compile(
    r"^\s*(?:static\s+)?(?:inline\s+)?[A-Za-z_][\w\s*]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:\{|$)"
)


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative: str
    component: str
    sha256: str
    text: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(source_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _component(relative: Path) -> str:
    parts = relative.parts
    if not parts:
        return "bundle"
    if parts[0] in {"apps", "libs", "tools"} and len(parts) > 1:
        return f"{parts[0]}-{parts[1]}"
    return parts[0]


def _submodule_records(source_root: Path, prefix: str = "") -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for line in _git(source_root, "ls-files", "--stage").splitlines():
        metadata, _, path = line.partition("\t")
        mode, sha, _stage = metadata.split()
        if mode != "160000":
            continue
        module_root = source_root / path
        full_path = f"{prefix}/{path}".strip("/")
        url = _git(
            source_root,
            "config",
            "-f",
            ".gitmodules",
            "--get",
            f"submodule.{path}.url",
        )
        records.append(
            {
                "path": full_path,
                "url": url,
                "commit": sha,
                "checked_out_commit": _git(module_root, "rev-parse", "HEAD"),
            }
        )
        records.extend(_submodule_records(module_root, full_path))
    return records


def _artifact_type(relative: str, suffix: str) -> str:
    lower = relative.lower().replace("\\", "/")
    name = Path(relative).name.lower()
    if any(token in lower for token in ("unit-test", "unit_test", "/tests/", "/test/")):
        return "verification"
    if "requirement" in lower or "req" in name or suffix == ".dox":
        return "requirement"
    if suffix in {".xml", ".eds"} or any(
        token in lower for token in ("msgdef", "interface", "/inc/", "topicid")
    ):
        return "interface"
    if any(token in lower for token in ("/config/", "mission_inc", "platform_inc", "sample_defs")):
        return "configuration"
    if suffix in {".md", ".txt"} or "/docs/" in lower:
        return "documentation"
    return "design"


def _iter_source_files(source_root: Path) -> Iterable[SourceFile]:
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_root)
        if any(part.lower() in EXCLUDED_PARTS for part in relative_path.parts):
            continue
        if path.name in {"LICENSE", "NOTICE"} or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.strip():
            continue
        relative = relative_path.as_posix()
        yield SourceFile(
            path=path,
            relative=relative,
            component=_component(relative_path),
            sha256=_sha256(raw),
            text=text,
        )


def _anchors(lines: list[str], suffix: str) -> list[tuple[int, str]]:
    anchors: list[tuple[int, str]] = [(0, "document")]
    for index, line in enumerate(lines):
        match = _HEADING.match(line)
        if match:
            anchors.append((index, match.group(1).strip()))
            continue
        if suffix in {".xml", ".eds"}:
            match = _XML_NAMED.match(line)
            if match:
                anchors.append((index, f"{match.group(1)}-{match.group(2)}"))
                continue
        if suffix in {".c", ".cc", ".cpp", ".h", ".hh", ".hpp"}:
            match = _C_SYMBOL.match(line)
            if match:
                anchors.append((index, match.group(1)))
    unique: dict[int, str] = {}
    for index, label in anchors:
        unique.setdefault(index, label)
    return sorted(unique.items())


def _windows(start: int, end: int, lines: list[str]) -> Iterable[tuple[int, int]]:
    cursor = start
    while cursor < end:
        stop = min(cursor + FALLBACK_LINES, end)
        candidate = "\n".join(lines[cursor:stop])
        while stop > cursor + 1 and (
            len(candidate) > MAX_CHUNK_CHARS
            or len(candidate.encode("utf-8")) > MAX_CHUNK_UTF8_BYTES
        ):
            stop -= 1
            candidate = "\n".join(lines[cursor:stop])
        yield cursor, stop
        if stop >= end:
            break
        cursor = max(stop - FALLBACK_OVERLAP, cursor + 1)


def ingest_checkout(source_root: Path) -> tuple[list[ArtifactSpan], dict[str, Any]]:
    root_commit = _git(source_root, "rev-parse", "HEAD")
    release_tag = _git(source_root, "describe", "--tags", "--exact-match")
    gitlinks = _submodule_records(source_root)
    if any(item["commit"] != item["checked_out_commit"] for item in gitlinks):
        raise RuntimeError("A cFS submodule checkout does not match its pinned gitlink")

    artifacts: list[ArtifactSpan] = []
    source_files: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    for source in _iter_source_files(source_root):
        lines = source.text.splitlines()
        source_files.append(
            {
                "path": source.relative,
                "sha256": source.sha256,
                "bytes": source.path.stat().st_size,
            }
        )
        anchors = _anchors(lines, source.path.suffix.lower())
        for anchor_index, (start, label) in enumerate(anchors):
            end = anchors[anchor_index + 1][0] if anchor_index + 1 < len(anchors) else len(lines)
            if not "\n".join(lines[start:end]).strip():
                continue
            for part, (window_start, window_end) in enumerate(_windows(start, end, lines), start=1):
                content = "\n".join(lines[window_start:window_end]).strip("\n")
                if not content.strip():
                    continue
                safe_label = _SAFE_ID.sub("-", label).strip("-")[:72] or "document"
                suffix = f"-p{part}" if part > 1 else ""
                source_id = (
                    f"CFS::{source.component}::{source.relative}::{safe_label}{suffix}::"
                    f"L{window_start + 1}-L{window_end}"
                )
                if source_id in source_ids:
                    raise RuntimeError(f"Duplicate generated source ID: {source_id}")
                source_ids.add(source_id)
                artifacts.append(
                    ArtifactSpan(
                        source_id=source_id,
                        type=_artifact_type(source.relative, source.path.suffix.lower()),
                        title=f"{source.component}: {label}",
                        path=source.relative,
                        start_line=window_start + 1,
                        end_line=window_end,
                        content=content,
                        component=source.component,
                        symbol=label if label != "document" else None,
                        source_file_sha256=source.sha256,
                        content_sha256=_sha256(content.encode("utf-8")),
                    )
                )
    artifacts.sort(key=lambda item: item.source_id)
    provenance = {
        "schema_version": 1,
        "baseline_id": "nasa-cfs-bundle-v7.0.1",
        "repository": "https://github.com/nasa/cFS.git",
        "release_tag": release_tag,
        "root_commit": root_commit,
        "submodules": gitlinks,
        "normalization": "UTF-8 text with CRLF/CR normalized to LF; source meaning unchanged",
        "chunking": {
            "maximum_characters": MAX_CHUNK_CHARS,
            "maximum_utf8_bytes": MAX_CHUNK_UTF8_BYTES,
            "boundary": "heading, C symbol/function, EDS named element, or line window",
            "overlap_lines": FALLBACK_OVERLAP,
        },
        "allowed_suffixes": sorted(ALLOWED_SUFFIXES),
        "excluded_path_parts": sorted(EXCLUDED_PARTS),
        "excluded_file_classes": [
            "binary or non-UTF-8 content",
            "build/generated output",
            "vendored dependencies",
            "repository metadata and CI configuration",
        ],
        "licenses": [
            {
                "path": path.relative_to(source_root).as_posix(),
                "sha256": _sha256(path.read_bytes()),
            }
            for path in sorted(source_root.rglob("LICENSE*"), key=lambda item: item.as_posix())
            if path.is_file() and ".git" not in path.relative_to(source_root).parts
        ],
        "source_files": source_files,
        "artifact_count": len(artifacts),
        "artifact_type_counts": dict(sorted(Counter(item.type for item in artifacts).items())),
    }
    return artifacts, provenance


def _write_raw_archive(source_root: Path, destination: Path) -> None:
    with (
        destination.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for source in _iter_source_files(source_root):
            content = source.path.read_bytes()
            info = tarfile.TarInfo(source.relative)
            info.size = len(content)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(content))


def write_corpus(source_root: Path, output_root: Path) -> dict[str, Any]:
    artifacts, provenance = ingest_checkout(source_root)
    nasa_root = output_root / "data" / "nasa"
    nasa_root.mkdir(parents=True, exist_ok=True)
    artifact_path = nasa_root / "cfs-v7.0.1-artifacts.jsonl.gz"
    with (
        artifact_path.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
    ):
        for artifact in artifacts:
            line = json.dumps(
                artifact.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            compressed.write(line.encode("utf-8") + b"\n")
    raw_archive_path = nasa_root / "cfs-v7.0.1-raw-sources.tar.gz"
    _write_raw_archive(source_root, raw_archive_path)
    provenance["artifact_package"] = {
        "path": "data/nasa/cfs-v7.0.1-artifacts.jsonl.gz",
        "sha256": _sha256(artifact_path.read_bytes()),
        "bytes": artifact_path.stat().st_size,
    }
    provenance["raw_source_archive"] = {
        "path": "data/nasa/cfs-v7.0.1-raw-sources.tar.gz",
        "sha256": _sha256(raw_archive_path.read_bytes()),
        "bytes": raw_archive_path.stat().st_size,
    }
    provenance_path = nasa_root / "cfs-v7.0.1-provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "artifacts": len(artifacts),
        "artifact_package": str(artifact_path),
        "artifact_package_sha256": provenance["artifact_package"]["sha256"],
        "provenance": str(provenance_path),
        "raw_source_archive": str(raw_archive_path),
        "type_counts": provenance["artifact_type_counts"],
    }


def load_corpus_package(path: Path) -> list[ArtifactSpan]:
    artifacts: list[ArtifactSpan] = []
    with gzip.open(path, mode="rt", encoding="utf-8", newline="\n") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                artifacts.append(ArtifactSpan.model_validate_json(line))
            except ValueError as error:
                raise ValueError(f"Invalid artifact row {line_number} in {path}") from error
    if not artifacts:
        raise ValueError(f"Artifact package is empty: {path}")
    source_ids = [item.source_id for item in artifacts]
    if source_ids != sorted(source_ids) or len(source_ids) != len(set(source_ids)):
        raise ValueError("Artifact package IDs must be unique and sorted")
    return artifacts
