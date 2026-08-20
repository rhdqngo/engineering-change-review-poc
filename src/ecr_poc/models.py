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
    """Historical result status retained for the v1-v5 offline adapter."""

    VERIFIED_REVIEW = "VERIFIED_REVIEW"
    NO_REVIEW = "NO_REVIEW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"


class CandidateFinalStatus(StrEnum):
    VERIFIED_REVIEW = "VERIFIED_REVIEW"
    NO_REVIEW = "NO_REVIEW"
    NO_SUPPORTED_CLAIM = "NO_SUPPORTED_CLAIM"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCKED = "BLOCKED"


class VerifierVerdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"  # historical log adapter only


class ImpactType(StrEnum):
    REQUIREMENT_CONFLICT = "REQUIREMENT_CONFLICT"
    INTERFACE_IMPACT = "INTERFACE_IMPACT"
    DESIGN_ASSUMPTION = "DESIGN_ASSUMPTION"
    CONFIGURATION_IMPACT = "CONFIGURATION_IMPACT"
    IMPLEMENTATION_IMPACT = "IMPLEMENTATION_IMPACT"
    VERIFICATION_IMPACT = "VERIFICATION_IMPACT"
    DOCUMENTATION_IMPACT = "DOCUMENTATION_IMPACT"


class IncomingArtifactType(StrEnum):
    REQUIREMENT = "requirement"
    INTERFACE_CHANGE = "interface_change"
    DESIGN_CHANGE = "design_change"
    CONFIGURATION_CHANGE = "configuration_change"
    VERIFICATION_CHANGE = "verification_change"
    DOCUMENTATION_CHANGE = "documentation_change"
    OTHER_ENGINEERING = "other_engineering"


class OverallReviewStatus(StrEnum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NO_SUPPORTED_REVIEW = "NO_SUPPORTED_REVIEW"
    INCONCLUSIVE = "INCONCLUSIVE"
    NO_REVIEW_FOUND = "NO_REVIEW_FOUND"  # historical v6 pre-design fixture adapter


class IncomingArtifact(StrictModel):
    artifact_type: IncomingArtifactType
    text: str = Field(min_length=1, max_length=20_000)
    title: str | None = Field(default=None, max_length=200)
    subsystem: str | None = Field(default=None, max_length=120)
    identifiers: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def normalize_user_fields(self) -> IncomingArtifact:
        self.text = self.text.strip()
        if not self.text:
            raise ValueError("Incoming artifact text must not be blank")
        self.title = self.title.strip() if self.title and self.title.strip() else None
        self.subsystem = (
            self.subsystem.strip() if self.subsystem and self.subsystem.strip() else None
        )
        normalized = [value.strip() for value in self.identifiers if value.strip()]
        if any(len(value) > 120 for value in normalized):
            raise ValueError("Incoming artifact identifiers must be at most 120 characters")
        self.identifiers = list(dict.fromkeys(normalized))
        return self


class StructuredChange(StrictModel):
    """Historical v1-v5 adapter; never used by the purpose-driven v6 pipeline."""

    artifact_or_subsystem: str = ""
    parameter: str = ""
    old_value: str | None = None
    new_value: str | None = None
    change_type: str = ""
    related_terms: list[str] = Field(default_factory=list)


class ExpectedEvidence(StrictModel):
    source_id: str
    spans: list[str] = Field(min_length=1)


class ExpectedClaimSlot(StrictModel):
    claim_slot_id: str
    source_id: str
    impact_type: ImpactType
    acceptable_exact_evidence_spans: list[str] = Field(min_length=1)


class CaseDefinition(StrictModel):
    id: str
    type: str
    scenario: str
    incoming_artifact: IncomingArtifact | None = None
    basis_source_ids: list[str] = Field(default_factory=list)
    expected_claims: list[ExpectedClaimSlot] = Field(default_factory=list)
    expected_review_targets: list[str] = Field(default_factory=list)
    expected_evidence_by_target: list[ExpectedEvidence] = Field(default_factory=list)
    # Historical adapter fields. Purpose-driven v6 never sends them to retrieval or Agents.
    change_text: str = ""
    changed_source_id: str | None = None
    original_content: str | None = None
    changed_content: str | None = None
    change: StructuredChange = Field(default_factory=StructuredChange)

    def evidence_for(self, source_id: str) -> str | None:
        for claim_slot in self.expected_claims:
            if claim_slot.source_id == source_id:
                return claim_slot.acceptable_exact_evidence_spans[0]
        for expected_evidence in self.expected_evidence_by_target:
            if expected_evidence.source_id == source_id:
                return expected_evidence.spans[0]
        return None

    def impact_type_for(self, source_id: str) -> ImpactType:
        for claim_slot in self.expected_claims:
            if claim_slot.source_id == source_id:
                return claim_slot.impact_type
        return ImpactType.IMPLEMENTATION_IMPACT


class ArtifactSpan(StrictModel):
    source_id: str
    type: str
    title: str
    path: str
    start_line: int
    end_line: int
    content: str
    component: str | None = None
    symbol: str | None = None
    source_file_sha256: str | None = None
    content_sha256: str | None = None


class QueryProcessingResult(StrictModel):
    processor_version: str
    extracted_identifiers: list[str]
    query_fingerprint: str
    query_text: str | None = Field(default=None, exclude=True)


class RetrievedCandidate(ArtifactSpan):
    rank: int
    bm25_score: float
    embedding_score: float
    hybrid_score: float
    retrieval_origins: list[str] = Field(default_factory=list)
    broad_rank: int | None = None
    relation_identifiers: list[str] = Field(default_factory=list)
    relation_score: float = 0.0
    final_score: float = 0.0


class RetrievalSummary(StrictModel):
    baseline_count: int
    broad_k: int
    broad_count: int
    broad_candidate_fingerprint: str
    relation_expansion_count: int
    expanded_count: int
    expanded_pool_fingerprint: str
    final_k: int
    final_docket_fingerprint: str


class RetrievalResult(StrictModel):
    query_processing: QueryProcessingResult
    summary: RetrievalSummary
    broad_candidates: list[RetrievedCandidate]
    expanded_candidates: list[RetrievedCandidate]
    final_docket: list[RetrievedCandidate]


class ReviewerClaimDraft(StrictModel):
    impact_type: ImpactType
    impact_claim: str = Field(min_length=1, max_length=500)
    evidence_exact_text: str = Field(min_length=1, max_length=2_000)
    evidence_start_line: int = Field(ge=1)
    evidence_end_line: int = Field(ge=1)

    @model_validator(mode="after")
    def valid_line_order(self) -> ReviewerClaimDraft:
        if self.evidence_end_line < self.evidence_start_line:
            raise ValueError("Evidence end line precedes start line")
        return self


class CandidateDecision(StrictModel):
    source_id: str
    decision: Decision
    claims: list[ReviewerClaimDraft] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def decision_claim_contract(self) -> CandidateDecision:
        if self.decision is Decision.REVIEW and not self.claims:
            raise ValueError("REVIEW requires one to three atomic claims")
        if self.decision is not Decision.REVIEW and self.claims:
            raise ValueError("Only REVIEW may contain atomic claims")
        return self


class CandidateDecisionBatch(StrictModel):
    decisions: list[CandidateDecision]

    @model_validator(mode="after")
    def request_claim_limit(self) -> CandidateDecisionBatch:
        if sum(len(item.claims) for item in self.decisions) > 20:
            raise ValueError("A review request may contain at most 20 claims")
        return self


class ValidatedClaim(StrictModel):
    claim_id: str
    source_id: str
    final_rank: int
    impact_type: ImpactType
    impact_claim: str
    evidence_exact_text: str
    evidence_start_line: int
    evidence_end_line: int


class ClaimVerification(StrictModel):
    claim_id: str
    verdict: VerifierVerdict
    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def current_verdict_contract(self) -> ClaimVerification:
        if self.verdict is VerifierVerdict.NOT_APPLICABLE:
            raise ValueError("Current claim verifier verdict must be SUPPORTED, REJECTED, or MISSING")
        return self


class ClaimVerificationBatch(StrictModel):
    verifications: list[ClaimVerification]


class VerifiedClaim(StrictModel):
    claim_id: str
    source_id: str
    impact_type: ImpactType
    impact_claim: str
    evidence_exact_text: str
    evidence_start_line: int
    evidence_end_line: int
    verifier_reason: str


class CandidateReviewResult(StrictModel):
    source_id: str
    status: CandidateFinalStatus
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    blocked_count: int = 0
    blocked_stages: list[str] = Field(default_factory=list)
    verifier_verdicts: list[VerifierVerdict] = Field(default_factory=list)


# Historical v1-v5 result models.
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
    raw_output: str = ""
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
    candidates: list[RetrievedCandidate]
    candidate_fingerprint: str
    embedding_index_fingerprint: str | None = None
    identifier_index_fingerprint: str | None = None
    query_processing: QueryProcessingResult | None = None
    retrieval: RetrievalSummary | None = None
    candidate_decisions: list[CandidateDecision] = Field(default_factory=list)
    claim_verifications: list[ClaimVerification] = Field(default_factory=list)
    candidate_results: list[CandidateReviewResult] = Field(default_factory=list)
    role_traces: list[RoleTrace] = Field(default_factory=list)
    expected_review_targets: list[str] = Field(default_factory=list)
    expected_claims: list[ExpectedClaimSlot] = Field(default_factory=list)
    broad_candidate_source_ids: list[str] = Field(default_factory=list)
    expanded_candidate_source_ids: list[str] = Field(default_factory=list)
    retrieval_hit: bool = False
    incoming_artifact: IncomingArtifact | None = None
    overall_status: OverallReviewStatus | None = None
    partial: bool = False
    # Historical result adapter fields.
    structured_change: StructuredChange = Field(default_factory=StructuredChange)
    baseline_candidate_source_ids: list[str] = Field(default_factory=list)
    proposed_candidate_source_ids: list[str] = Field(default_factory=list)
    proposed_reviews: list[ReviewItem] = Field(default_factory=list)
    final_reviews: list[FinalReview] = Field(default_factory=list)


class LiveReviewRequest(StrictModel):
    incoming_artifact: IncomingArtifact


class LiveReviewResponse(StrictModel):
    request_id: str
    baseline_id: str
    provider: str
    model: str
    embedding_model: str
    embedding_index_fingerprint: str
    identifier_index_fingerprint: str
    query_processing: QueryProcessingResult
    retrieval: RetrievalSummary
    final_docket: list[RetrievedCandidate]
    candidate_results: list[CandidateReviewResult]
    overall_status: OverallReviewStatus
    partial: bool
    retention: str = "not_saved"


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
    identifier_index_manifest: str | None = None
    identifier_index_manifest_sha256: str | None = None
    identifier_index_fingerprint: str | None = None
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
        match = re.search(r"-v([0-9]+)(?:-|$)", self.experiment_id)
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
    request_id: str | None = None
    case_id: str | None = None
    artifact_type: IncomingArtifactType | None = None
    overall_status: OverallReviewStatus | None = None
    role: str | None = None
    model: str | None = None
    source_id: str | None = None
    claim_id: str | None = None
    decision: Decision | FinalStatus | CandidateFinalStatus | None = None
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
