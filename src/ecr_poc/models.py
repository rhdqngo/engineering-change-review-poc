from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Decision(StrEnum):
    REVIEW = "REVIEW"
    NO_REVIEW = "NO_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FinalStatus(StrEnum):
    VERIFIED_REVIEW = "VERIFIED_REVIEW"
    NO_REVIEW = "NO_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"


class VerifierVerdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StructuredChange(StrictModel):
    artifact_or_subsystem: str
    parameter: str
    old_value: str | None = None
    new_value: str | None = None
    change_type: str
    related_terms: list[str] = Field(default_factory=list)


class ExpectedEvidence(StrictModel):
    source_id: str
    spans: list[str] = Field(min_length=1)


class CaseDefinition(StrictModel):
    id: str
    type: str
    scenario: str
    change_text: str
    changed_source_id: str
    original_content: str
    changed_content: str
    change: StructuredChange
    expected_review_targets: list[str]
    expected_evidence_by_target: list[ExpectedEvidence] = Field(default_factory=list)

    def evidence_for(self, source_id: str) -> str | None:
        for expected in self.expected_evidence_by_target:
            if expected.source_id == source_id:
                return expected.spans[0]
        return None


class ArtifactSpan(StrictModel):
    source_id: str
    type: str
    title: str
    path: str
    start_line: int
    end_line: int
    content: str


class RetrievedCandidate(ArtifactSpan):
    rank: int
    bm25_score: float
    embedding_score: float
    hybrid_score: float


class ReviewItem(StrictModel):
    source_id: str
    decision: Decision
    evidence: str | None = None
    short_reason: str

    @model_validator(mode="after")
    def review_requires_evidence(self) -> ReviewItem:
        if self.decision is Decision.REVIEW and not self.evidence:
            raise ValueError("REVIEW requires a non-empty evidence span")
        return self


class ReviewBatch(StrictModel):
    reviews: list[ReviewItem]


class VerificationItem(StrictModel):
    source_id: str
    supported: bool
    reason: str


class VerificationBatch(StrictModel):
    verifications: list[VerificationItem]


class FinalReview(StrictModel):
    source_id: str
    status: FinalStatus
    evidence: str | None = None
    short_reason: str
    verifier_reason: str | None = None
    blocked_stage: str | None = None


class RoleTrace(StrictModel):
    role: str
    provider: str
    model: str
    raw_output: str
    parsed: dict[str, Any] | list[Any] | None = None
    error: str | None = None


class PipelineResult(StrictModel):
    run_id: str
    case_id: str
    case_type: str
    scenario: str
    provider: str
    model: str
    embedding_model: str
    started_at: str
    completed_at: str
    structured_change: StructuredChange
    candidates: list[RetrievedCandidate]
    candidate_fingerprint: str
    embedding_index_fingerprint: str | None = None
    baseline_candidate_source_ids: list[str]
    proposed_candidate_source_ids: list[str]
    proposed_reviews: list[ReviewItem]
    final_reviews: list[FinalReview]
    role_traces: list[RoleTrace]
    expected_review_targets: list[str]
    retrieval_hit: bool


class RunProvenance(StrictModel):
    source_commit: str
    freeze_tag: str
    experiment_manifest: str | None = None
    prompt_version: str
    prompt_hashes: dict[str, str]
    input_manifest_sha256: str
    embedding_index_manifest: str | None = None
    embedding_index_manifest_sha256: str | None = None
    embedding_index_fingerprint: str | None = None
    artifact_store: str
    cloud_execution: str | None = None
    container_image_digest: str | None = None
    adk_version: str | None = None


class EvaluationRun(StrictModel):
    experiment_id: str
    run_id: str
    provider: str
    model: str
    embedding_model: str
    started_at: str
    completed_at: str
    freeze_hashes: dict[str, str]
    configuration: dict[str, Any]
    cases: list[PipelineResult]
    metrics: dict[str, Any]
    provenance: RunProvenance | None = None

    @model_validator(mode="after")
    def versioned_runs_require_provenance(self) -> EvaluationRun:
        prefix = "ecr-poc-preregistered-v"
        if self.experiment_id.startswith(prefix):
            version_text = self.experiment_id.removeprefix(prefix)
            match = re.match(r"([0-9]+)(?:-|$)", version_text)
            if match is not None and int(match.group(1)) >= 2:
                version = int(match.group(1))
                if self.provenance is None:
                    raise ValueError("Versioned evaluation runs require provenance")
                if version >= 3 and not self.provenance.experiment_manifest:
                    raise ValueError(
                        "v3 and later evaluation runs require an experiment manifest"
                    )
        return self


class PublishedPointer(StrictModel):
    run_id: str
    experiment_id: str
    object_name: str
    generation: int
    sha256: str
    published_at: str
    source_commit: str
    experiment_manifest: str | None = None


class DecisionLogEvent(StrictModel):
    event: str
    severity: str = "INFO"
    timestamp: str
    run_id: str | None = None
    case_id: str | None = None
    role: str | None = None
    model: str | None = None
    source_id: str | None = None
    decision: Decision | FinalStatus | None = None
    verifier_verdict: VerifierVerdict | None = None
    candidate_fingerprint: str | None = None
    verified: int | None = None
    blocked: int | None = None
    blocked_stage: str | None = None
    latency_ms: int | None = None
    error_type: str | None = None
    failure_write_error_type: str | None = None
    cases: int | None = None
    completed_cases: int | None = None
