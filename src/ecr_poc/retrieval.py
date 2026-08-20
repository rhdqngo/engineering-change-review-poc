from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import Protocol

from google import genai
from google.genai import types

from .data import load_artifacts, repository_root
from .models import ArtifactSpan, RetrievedCandidate, StructuredChange

_WORD = re.compile(r"[A-Za-z]+(?:[A-Z][a-z]+)*|[0-9]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def tokenize(text: str) -> list[str]:
    normalized = text.replace("_", " ").replace("/", " ").replace("-", " ")
    tokens: list[str] = []
    for raw in _WORD.findall(normalized):
        pieces = _CAMEL.sub(" ", raw).split()
        tokens.extend(piece.lower() for piece in pieces if piece)
        if len(pieces) > 1:
            tokens.append(raw.lower())
    return tokens


class Embedder(Protocol):
    model_name: str

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class DeterministicHashEmbedder:
    """Offline deterministic dense vectors for tests and UI fixtures, not LLM results."""

    model_name = "deterministic-hash-embedding-v1"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        features = tokens + [f"{a}::{b}" for a, b in pairwise(tokens)]
        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class VertexEmbedder:
    model_name: str

    def __init__(
        self,
        project: str,
        location: str = "global",
        model_name: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
        cache_path: Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.output_dimensionality = output_dimensionality
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.cache_path = cache_path or (
            repository_root() / ".cache" / "ecr-poc" / "vertex-embeddings.json"
        )
        self._cache = self._read_cache()

    def _read_cache(self) -> dict[str, list[float]]:
        if not self.cache_path.exists():
            return {}
        with self.cache_path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}

    def _write_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self._cache, handle, separators=(",", ":"))
        temporary.replace(self.cache_path)

    def _key(self, purpose: str, text: str) -> str:
        payload = f"{self.model_name}|{self.output_dimensionality}|{purpose}|{text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _embed(self, texts: Sequence[str], purpose: str) -> list[list[float]]:
        keys = [self._key(purpose, text) for text in texts]
        missing = [(key, text) for key, text in zip(keys, texts) if key not in self._cache]
        task_type = "RETRIEVAL_DOCUMENT" if purpose == "document" else "RETRIEVAL_QUERY"
        for offset in range(0, len(missing), 100):
            batch = missing[offset : offset + 100]
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=[text for _, text in batch],
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.output_dimensionality,
                    auto_truncate=False,
                ),
            )
            if not response.embeddings or len(response.embeddings) != len(batch):
                raise RuntimeError("Vertex embedding response count mismatch")
            for (key, _), embedding in zip(batch, response.embeddings):
                if not embedding.values:
                    raise RuntimeError("Vertex embedding response had no values")
                self._cache[key] = [float(value) for value in embedding.values]
        if missing:
            self._write_cache()
        return [self._cache[key] for key in keys]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "document")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "query")[0]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _min_max(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


class HybridRetriever:
    def __init__(
        self,
        artifacts: Sequence[ArtifactSpan],
        embedder: Embedder,
        lexical_weight: float = 0.5,
        embedding_weight: float = 0.5,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not math.isclose(lexical_weight + embedding_weight, 1.0):
            raise ValueError("Hybrid weights must sum to 1")
        self.artifacts = list(artifacts)
        self.embedder = embedder
        self.lexical_weight = lexical_weight
        self.embedding_weight = embedding_weight
        self.k1 = k1
        self.b = b
        self._tokens = [tokenize(f"{item.title}\n{item.content}") for item in self.artifacts]
        self._lengths = [len(tokens) for tokens in self._tokens]
        self._avg_length = sum(self._lengths) / max(len(self._lengths), 1)
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            self._document_frequency.update(set(tokens))
        self._document_embeddings = embedder.embed_documents(
            [f"{item.title}\n{item.content}" for item in self.artifacts]
        )

    def _bm25(self, query_tokens: Sequence[str], index: int) -> float:
        frequencies = Counter(self._tokens[index])
        score = 0.0
        document_count = len(self.artifacts)
        length = self._lengths[index]
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            document_frequency = self._document_frequency[token]
            inverse_document_frequency = math.log(
                1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * length / max(self._avg_length, 1)
            )
            score += inverse_document_frequency * frequency * (self.k1 + 1) / denominator
        return score

    def retrieve(self, change: StructuredChange, top_k: int) -> list[RetrievedCandidate]:
        query = "\n".join(
            part
            for part in [
                change.artifact_or_subsystem,
                change.parameter,
                change.old_value,
                change.new_value,
                change.change_type,
                " ".join(change.related_terms),
            ]
            if part
        )
        query_tokens = tokenize(query)
        query_embedding = self.embedder.embed_query(query)
        bm25_scores = [self._bm25(query_tokens, index) for index in range(len(self.artifacts))]
        embedding_scores = [
            _cosine(query_embedding, embedding) for embedding in self._document_embeddings
        ]
        normalized_bm25 = _min_max(bm25_scores)
        normalized_embeddings = _min_max(embedding_scores)
        hybrid_scores = [
            self.lexical_weight * lexical + self.embedding_weight * semantic
            for lexical, semantic in zip(normalized_bm25, normalized_embeddings)
        ]
        ordered = sorted(
            range(len(self.artifacts)),
            key=lambda index: (-hybrid_scores[index], self.artifacts[index].source_id),
        )[:top_k]
        candidates: list[RetrievedCandidate] = []
        for rank, index in enumerate(ordered, start=1):
            artifact = self.artifacts[index]
            candidates.append(
                RetrievedCandidate(
                    **artifact.model_dump(),
                    rank=rank,
                    bm25_score=round(bm25_scores[index], 8),
                    embedding_score=round(embedding_scores[index], 8),
                    hybrid_score=round(hybrid_scores[index], 8),
                )
            )
        return candidates


def candidate_fingerprint(candidates: Sequence[RetrievedCandidate]) -> str:
    identity = [
        {
            "rank": item.rank,
            "source_id": item.source_id,
            "content_sha256": hashlib.sha256(item.content.encode("utf-8")).hexdigest(),
        }
        for item in candidates
    ]
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_embedder(provider: str) -> Embedder:
    if provider == "vertex":
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Vertex embeddings")
        return VertexEmbedder(
            project=project,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            model_name=os.environ.get("ECR_EMBEDDING_MODEL", "gemini-embedding-001"),
        )
    if provider == "local":
        return DeterministicHashEmbedder()
    raise ValueError(f"Unknown embedding provider: {provider}")


def hybrid_retrieval_tool(query: str, top_k: int = 6) -> dict[str, object]:
    """Return fixed hybrid-retrieval candidates for an already normalized change.

    This public ADK-compatible function is a deterministic shared tool, not an
    agent. `query` becomes the normalized parameter and related term input.
    Production evaluation uses `HybridRetriever` directly so both experiment
    arms share the exact candidate objects and fingerprint.
    """
    change = StructuredChange(
        artifact_or_subsystem="SAMPLE_APP",
        parameter=query,
        change_type="query",
        related_terms=tokenize(query),
    )
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    candidates = retriever.retrieve(change, top_k)
    return {
        "candidate_fingerprint": candidate_fingerprint(candidates),
        "candidates": [candidate.model_dump() for candidate in candidates],
    }
