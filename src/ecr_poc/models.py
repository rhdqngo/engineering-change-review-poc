from __future__ import annotations

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


class StructuredChange(StrictModel):
    artifact_or_subsystem: str
    parameter: str
    old_value: str | None = None
    new_value: str | None = None
    change_type: str
    related_terms: list[str] = Field(default_factory=list)


class ExpectedEvidence(StrictModel):
    source_id: str
    span: str


class CaseDefinition(StrictModel):
    id: str
    type: str
    scenario: str
    change_text: str
    change: StructuredChange
    expected_review_targets: list[str]
    expected_evidence: ExpectedEvidence | None = None


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
            if version_text.isdigit() and int(version_text) >= 2:
                if self.provenance is None:
                    raise ValueError("Versioned evaluation runs require provenance")
                if int(version_text) >= 3 and not self.provenance.experiment_manifest:
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
