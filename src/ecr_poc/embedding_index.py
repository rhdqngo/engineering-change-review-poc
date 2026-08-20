from __future__ import annotations

import hashlib
import json
import sys
from array import array
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .data import sha256_file
from .models import ArtifactSpan

MAX_EMBEDDING_INPUT_UTF8_BYTES = 2_000


class DocumentEmbedder(Protocol):
    model_name: str

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class FrozenEmbeddingIndex:
    model_name: str
    dimensions: int
    fingerprint: str
    vectors: list[memoryview]


def _source_ids_sha256(artifacts: Sequence[ArtifactSpan]) -> str:
    payload = "\n".join(item.source_id for item in artifacts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_embedding_index(
    artifacts: Sequence[ArtifactSpan],
    embedder: DocumentEmbedder,
    output_root: Path,
    *,
    experiment_id: str,
    dimensions: int,
    artifact_package_sha256: str,
) -> dict[str, Any]:
    texts = [f"{item.title}\n{item.content}" for item in artifacts]
    oversized = [
        item.source_id
        for item, text in zip(artifacts, texts)
        if len(text.encode("utf-8")) > MAX_EMBEDDING_INPUT_UTF8_BYTES
    ]
    if oversized:
        raise RuntimeError(
            "Embedding serialization exceeds the preflight UTF-8 byte envelope: "
            f"{oversized[0]}"
        )
    vectors = embedder.embed_documents(texts)
    if len(vectors) != len(artifacts):
        raise RuntimeError("Embedding vector count does not match artifact count")
    flat = array("f")
    for source_id, vector in zip((item.source_id for item in artifacts), vectors):
        if len(vector) != dimensions:
            raise RuntimeError(
                f"Embedding dimensions for {source_id} are {len(vector)}, expected {dimensions}"
            )
        flat.extend(float(value) for value in vector)
    if sys.byteorder != "little":
        flat.byteswap()
    embedding_root = output_root / "data" / "embeddings"
    embedding_root.mkdir(parents=True, exist_ok=True)
    vector_path = embedding_root / "ecr-poc-v6-vectors.f32"
    vector_path.write_bytes(flat.tobytes())
    vector_sha = sha256_file(vector_path)
    source_ids_sha = _source_ids_sha256(artifacts)
    identity = {
        "model": embedder.model_name,
        "dimensions": dimensions,
        "source_ids_sha256": source_ids_sha,
        "vector_sha256": vector_sha,
    }
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    metadata = {
        "schema_version": 2,
        "experiment_id": experiment_id,
        "embedding_model": embedder.model_name,
        "output_dimensionality": dimensions,
        "task_types": {"documents": "RETRIEVAL_DOCUMENT", "queries": "RETRIEVAL_QUERY"},
        "document_serialization": "UTF-8 title + LF + exact artifact content in source_id order",
        "document_input_max_utf8_bytes": MAX_EMBEDDING_INPUT_UTF8_BYTES,
        "artifact_package_sha256": artifact_package_sha256,
        "artifact_count": len(artifacts),
        "source_ids_sha256": source_ids_sha,
        "vector_file": "data/embeddings/ecr-poc-v6-vectors.f32",
        "vector_file_sha256": vector_sha,
        "vector_format": "little-endian IEEE-754 float32 row-major",
        "vector_fingerprint": fingerprint,
    }
    metadata_path = embedding_root / "ecr-poc-v6.json"
    metadata_path.write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def load_embedding_index(
    root: Path,
    metadata_relative: str,
    artifacts: Sequence[ArtifactSpan],
) -> FrozenEmbeddingIndex:
    metadata_path = root / metadata_relative
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    vector_path = root / str(metadata["vector_file"])
    if sha256_file(vector_path) != metadata["vector_file_sha256"]:
        raise RuntimeError("Frozen embedding vector SHA-256 mismatch")
    if int(metadata["artifact_count"]) != len(artifacts):
        raise RuntimeError("Frozen embedding artifact count mismatch")
    if metadata["source_ids_sha256"] != _source_ids_sha256(artifacts):
        raise RuntimeError("Frozen embedding source ordering mismatch")
    dimensions = int(metadata["output_dimensionality"])
    values = array("f")
    values.frombytes(vector_path.read_bytes())
    if sys.byteorder != "little":
        values.byteswap()
    expected_values = len(artifacts) * dimensions
    if len(values) != expected_values:
        raise RuntimeError(
            f"Frozen embedding value count is {len(values)}, expected {expected_values}"
        )
    view = memoryview(values)
    rows = [view[index * dimensions : (index + 1) * dimensions] for index in range(len(artifacts))]
    return FrozenEmbeddingIndex(
        model_name=str(metadata["embedding_model"]),
        dimensions=dimensions,
        fingerprint=str(metadata["vector_fingerprint"]),
        vectors=rows,
    )
