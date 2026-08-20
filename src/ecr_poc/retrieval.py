from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import Protocol

from google import genai
from google.genai import types

from .identifier_index import (
    IdentifierIndex,
    build_identifier_index,
    identifier_specificity,
)
from .models import (
    ArtifactSpan,
    IncomingArtifact,
    RetrievalResult,
    RetrievalSummary,
    RetrievedCandidate,
)
from .query_processing import process_query

BROAD_K = 40
FINAL_K = 10
MAX_EXPANDED_POOL = 200
MAX_RELATION_CANDIDATES = MAX_EXPANDED_POOL - BROAD_K
HYBRID_FINAL_WEIGHT = 0.75
RELATION_FINAL_WEIGHT = 0.25

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
    """Offline deterministic dense vectors for tests and UI fixtures only."""

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
        return [value / norm for value in vector] if norm else vector

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
        from .data import repository_root

        self.cache_path = cache_path or (
            repository_root() / ".cache" / "ecr-poc" / "vertex-embeddings.json"
        )
        self._cache = self._read_cache()

    def _read_cache(self) -> dict[str, list[float]]:
        cache: dict[str, list[float]] = {}
        candidates = [self.cache_path]
        parts = self.cache_path.with_suffix(".parts")
        if parts.is_dir():
            candidates.extend(sorted(parts.glob("*.json")))
        for candidate in candidates:
            if not candidate.is_file():
                continue
            with candidate.open(encoding="utf-8") as handle:
                value = json.load(handle)
            if not isinstance(value, dict):
                continue
            for key, vector in value.items():
                if isinstance(key, str) and isinstance(vector, list):
                    cache[key] = [float(item) for item in vector]
        return cache

    def _write_cache_batch(self, entries: dict[str, list[float]]) -> None:
        parts = self.cache_path.with_suffix(".parts")
        parts.mkdir(parents=True, exist_ok=True)
        fingerprint = hashlib.sha256(
            "\n".join(sorted(entries)).encode("ascii")
        ).hexdigest()
        destination = parts / f"{fingerprint}.json"
        if destination.exists():
            return
        temporary = parts / f"{fingerprint}.tmp"
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(entries, handle, separators=(",", ":"))
        temporary.replace(destination)

    def _key(self, purpose: str, text: str) -> str:
        payload = f"{self.model_name}|{self.output_dimensionality}|{purpose}|{text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _embed(
        self, texts: Sequence[str], purpose: str, *, use_cache: bool = True
    ) -> list[list[float]]:
        keys = [self._key(purpose, text) for text in texts]
        resolved = dict(self._cache) if use_cache else {}
        missing_by_key: dict[str, str] = {}
        for key, text in zip(keys, texts):
            if key not in resolved:
                missing_by_key.setdefault(key, text)
        missing = list(missing_by_key.items())
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
            completed: dict[str, list[float]] = {}
            for (key, _), embedding in zip(batch, response.embeddings):
                if not embedding.values:
                    raise RuntimeError("Vertex embedding response had no values")
                completed[key] = [float(value) for value in embedding.values]
            resolved.update(completed)
            if use_cache:
                self._cache.update(completed)
                self._write_cache_batch(completed)
        return [resolved[key] for key in keys]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(texts, "document")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "query", use_cache=False)[0]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _min_max(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


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


class HybridRetriever:
    def __init__(
        self,
        artifacts: Sequence[ArtifactSpan],
        embedder: Embedder,
        lexical_weight: float = 0.5,
        embedding_weight: float = 0.5,
        k1: float = 1.5,
        b: float = 0.75,
        document_embeddings: Sequence[Sequence[float]] | None = None,
        embedding_index_fingerprint: str | None = None,
        identifier_index: IdentifierIndex | None = None,
    ) -> None:
        if not math.isclose(lexical_weight + embedding_weight, 1.0):
            raise ValueError("Hybrid weights must sum to 1")
        self.artifacts = list(artifacts)
        self.embedder = embedder
        self.lexical_weight = lexical_weight
        self.embedding_weight = embedding_weight
        self.k1 = k1
        self.b = b
        self.identifier_index = identifier_index or build_identifier_index(self.artifacts)
        self.identifier_index_fingerprint = self.identifier_index.fingerprint
        self._by_id = {artifact.source_id: index for index, artifact in enumerate(self.artifacts)}
        self._tokens = [tokenize(f"{item.title}\n{item.content}") for item in self.artifacts]
        self._lengths = [len(tokens) for tokens in self._tokens]
        self._avg_length = sum(self._lengths) / max(len(self._lengths), 1)
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            self._document_frequency.update(set(tokens))
        self._document_embeddings: Sequence[Sequence[float]]
        if document_embeddings is None:
            self._document_embeddings = embedder.embed_documents(
                [f"{item.title}\n{item.content}" for item in self.artifacts]
            )
            identity = {
                "model": embedder.model_name,
                "sources": [item.source_id for item in self.artifacts],
                "vectors": self._document_embeddings,
            }
            self.embedding_index_fingerprint = hashlib.sha256(
                json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        else:
            if len(document_embeddings) != len(self.artifacts):
                raise ValueError("Frozen document vector count does not match artifacts")
            if not embedding_index_fingerprint:
                raise ValueError("Frozen document vectors require an index fingerprint")
            self._document_embeddings = document_embeddings
            self.embedding_index_fingerprint = embedding_index_fingerprint

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
                1
                + (document_count - document_frequency + 0.5)
                / (document_frequency + 0.5)
            )
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * length / max(self._avg_length, 1)
            )
            score += (
                inverse_document_frequency
                * frequency
                * (self.k1 + 1)
                / denominator
            )
        return score

    def retrieve(
        self,
        incoming: IncomingArtifact,
        final_k: int = FINAL_K,
        broad_k: int = BROAD_K,
    ) -> RetrievalResult:
        if broad_k != BROAD_K or final_k != FINAL_K:
            raise ValueError("Purpose-driven v6 requires Broad Top-40 and Final Top-10")
        query = process_query(incoming)
        if query.query_text is None:
            raise RuntimeError("Deterministic query serialization is unavailable")
        query_tokens = list(dict.fromkeys(tokenize(query.query_text)))
        query_embedding = self.embedder.embed_query(query.query_text)
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
        broad_indexes = sorted(
            range(len(self.artifacts)),
            key=lambda index: (-hybrid_scores[index], self.artifacts[index].source_id),
        )[:broad_k]
        broad_ranks = {index: rank for rank, index in enumerate(broad_indexes, start=1)}

        relation_edges: dict[int, dict[str, float]] = defaultdict(dict)
        corpus_size = len(self.artifacts)
        for identifier in query.extracted_identifiers:
            for entry in self.identifier_index.eligible_entries(identifier):
                specificity = identifier_specificity(
                    entry.document_frequency, corpus_size
                )
                for source_id in entry.postings:
                    index = self._by_id[source_id]
                    relation_edges[index][identifier] = max(
                        relation_edges[index].get(identifier, 0.0), specificity
                    )
        for broad_index, broad_rank in broad_ranks.items():
            seed_strength = 1 / math.log2(broad_rank + 1)
            for identifier in self.identifier_index.seed_identifiers(
                self.artifacts[broad_index].source_id, corpus_size
            ):
                for entry in self.identifier_index.eligible_entries(identifier):
                    edge_score = seed_strength * identifier_specificity(
                        entry.document_frequency, corpus_size
                    )
                    for source_id in entry.postings:
                        index = self._by_id[source_id]
                        relation_edges[index][identifier] = max(
                            relation_edges[index].get(identifier, 0.0), edge_score
                        )

        relation_scores = {
            index: max(edges.values(), default=0.0)
            for index, edges in relation_edges.items()
        }
        broad_set = set(broad_indexes)
        relation_only = sorted(
            (index for index in relation_scores if index not in broad_set),
            key=lambda index: (
                -relation_scores[index],
                -hybrid_scores[index],
                self.artifacts[index].source_id,
            ),
        )[:MAX_RELATION_CANDIDATES]
        pool_indexes = broad_indexes + relation_only
        final_scores = {
            index: HYBRID_FINAL_WEIGHT * hybrid_scores[index]
            + RELATION_FINAL_WEIGHT * relation_scores.get(index, 0.0)
            for index in pool_indexes
        }
        expanded_indexes = sorted(
            pool_indexes,
            key=lambda index: (
                -final_scores[index],
                -hybrid_scores[index],
                self.artifacts[index].source_id,
            ),
        )

        def make_candidate(index: int, rank: int) -> RetrievedCandidate:
            artifact = self.artifacts[index]
            origins: list[str] = []
            if bm25_scores[index] > 0:
                origins.append("lexical")
            origins.append("dense")
            relation_identifiers = sorted(relation_edges.get(index, {}))
            if relation_identifiers:
                origins.append("relation_expansion")
            return RetrievedCandidate(
                **artifact.model_dump(),
                rank=rank,
                bm25_score=round(bm25_scores[index], 8),
                embedding_score=round(embedding_scores[index], 8),
                hybrid_score=round(hybrid_scores[index], 8),
                retrieval_origins=origins,
                broad_rank=broad_ranks.get(index),
                relation_identifiers=relation_identifiers,
                relation_score=round(relation_scores.get(index, 0.0), 8),
                final_score=round(final_scores.get(index, hybrid_scores[index]), 8),
            )

        broad_candidates = [
            make_candidate(index, rank)
            for rank, index in enumerate(broad_indexes, start=1)
        ]
        expanded_candidates = [
            make_candidate(index, rank)
            for rank, index in enumerate(expanded_indexes, start=1)
        ]
        final_docket = [
            make_candidate(index, rank)
            for rank, index in enumerate(expanded_indexes[:final_k], start=1)
        ]
        summary = RetrievalSummary(
            baseline_count=len(self.artifacts),
            broad_k=broad_k,
            broad_count=len(broad_candidates),
            broad_candidate_fingerprint=candidate_fingerprint(broad_candidates),
            relation_expansion_count=len(relation_only),
            expanded_count=len(expanded_candidates),
            expanded_pool_fingerprint=candidate_fingerprint(expanded_candidates),
            final_k=final_k,
            final_docket_fingerprint=candidate_fingerprint(final_docket),
        )
        return RetrievalResult(
            query_processing=query,
            summary=summary,
            broad_candidates=broad_candidates,
            expanded_candidates=expanded_candidates,
            final_docket=final_docket,
        )


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


def hybrid_retrieval_tool(
    artifact_type: str, text: str, top_k: int = FINAL_K
) -> dict[str, object]:
    """Deterministic local demonstration tool, never an Agent."""

    from .data import load_artifacts
    from .models import IncomingArtifactType

    incoming = IncomingArtifact(
        artifact_type=IncomingArtifactType(artifact_type),
        text=text,
    )
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    result = retriever.retrieve(incoming, final_k=top_k)
    return {
        "broad_candidate_fingerprint": result.summary.broad_candidate_fingerprint,
        "expanded_pool_fingerprint": result.summary.expanded_pool_fingerprint,
        "final_docket_fingerprint": result.summary.final_docket_fingerprint,
        "candidates": [candidate.model_dump() for candidate in result.final_docket],
    }
