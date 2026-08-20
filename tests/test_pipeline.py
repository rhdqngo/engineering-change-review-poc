import asyncio

import pytest

from ecr_poc.data import load_artifacts, load_cases
from ecr_poc.models import (
    Decision,
    FinalStatus,
    ReviewBatch,
    ReviewItem,
    VerificationBatch,
    VerificationItem,
)
from ecr_poc.pipeline import run_case
from ecr_poc.providers import FixtureProvider
from ecr_poc.retrieval import DeterministicHashEmbedder, HybridRetriever


def setup_case(case_id: str):
    _, top_k, cases = load_cases()
    case = next(item for item in cases if item.id == case_id)
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    return case, top_k, retriever


def test_baseline_and_proposed_reuse_identical_top_k() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, FixtureProvider(), top_k))
    assert result.baseline_candidate_source_ids == result.proposed_candidate_source_ids
    assert len(result.baseline_candidate_source_ids) == top_k
    assert any(
        item.source_id == "CONFIG_FUNCTION_CODES"
        and item.status is FinalStatus.VERIFIED_REVIEW
        for item in result.final_reviews
    )


def test_all_18_cases_share_candidate_sequence_object_and_fingerprint() -> None:
    _, top_k, cases = load_cases()
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    results = [
        asyncio.run(run_case(case, retriever, FixtureProvider(), top_k))
        for case in cases
    ]
    assert len(results) == 18
    for result in results:
        candidate_ids = [candidate.source_id for candidate in result.candidates]
        assert result.baseline_candidate_source_ids == candidate_ids
        assert result.proposed_candidate_source_ids == candidate_ids
        assert result.embedding_index_fingerprint == retriever.embedding_index_fingerprint


def test_non_exact_evidence_is_blocked_before_verifier() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(
        run_case(case, retriever, FixtureProvider(inject_unsupported=True), top_k)
    )
    blocked = [
        item
        for item in result.final_reviews
        if item.status is FinalStatus.REJECTED_UNSUPPORTED
    ]
    assert len(blocked) == 1
    assert blocked[0].blocked_stage == "deterministic_exact_span"
    assert blocked[0].evidence is None
    assert all(
        item.evidence != "THIS SPAN DOES NOT EXIST IN THE NASA SOURCE"
        for item in result.final_reviews
        if item.status is FinalStatus.VERIFIED_REVIEW
    )


class RejectingVerifierProvider(FixtureProvider):
    async def verify(self, case, change, proposals, candidates):
        batch = VerificationBatch(
            verifications=[
                VerificationItem(
                    source_id=proposal.source_id,
                    supported=False,
                    reason="Independent verifier found no entailment.",
                )
                for proposal in proposals
            ]
        )
        _, trace = await super().verify(case, change, proposals, candidates)
        return batch, trace


class DuplicateVerifierProvider(FixtureProvider):
    async def verify(self, case, change, proposals, candidates):
        proposal = proposals[0]
        batch = VerificationBatch(
            verifications=[
                VerificationItem(
                    source_id=proposal.source_id,
                    supported=True,
                    reason="First verdict.",
                ),
                VerificationItem(
                    source_id=proposal.source_id,
                    supported=True,
                    reason="Duplicate verdict.",
                ),
            ]
        )
        _, trace = await super().verify(case, change, proposals, candidates)
        return batch, trace


class FailingReviewProvider(FixtureProvider):
    async def review(self, case, change, candidates):
        raise RuntimeError("simulated provider outage")


class IncompleteReviewProvider(FixtureProvider):
    async def review(self, case, change, candidates):
        batch, trace = await super().review(case, change, candidates)
        incomplete = ReviewBatch(reviews=batch.reviews[:1])
        return incomplete, trace


class DuplicateAndExternalReviewProvider(FixtureProvider):
    async def review(self, case, change, candidates):
        batch, trace = await super().review(case, change, candidates)
        malformed = ReviewBatch(
            reviews=[
                *batch.reviews,
                batch.reviews[0],
                ReviewItem(
                    source_id="OUTSIDE_FIXED_TOP_K",
                    decision=Decision.NO_REVIEW,
                    short_reason="This source was not retrieved.",
                ),
            ]
        )
        return malformed, trace


class MissingVerifierProvider(FixtureProvider):
    async def verify(self, case, change, proposals, candidates):
        _, trace = await super().verify(case, change, proposals, candidates)
        return VerificationBatch(verifications=[]), trace


class SlowAnalystProvider(FixtureProvider):
    async def analyze(self, case):
        await asyncio.sleep(0.05)
        return await super().analyze(case)


def test_independent_verifier_rejection_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, RejectingVerifierProvider(), top_k))
    target = next(
        item for item in result.final_reviews if item.source_id == "CONFIG_FUNCTION_CODES"
    )
    assert target.status is FinalStatus.REJECTED_UNSUPPORTED
    assert target.blocked_stage == "independent_verifier"
    assert target.evidence is None


def test_duplicate_verifier_verdict_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, DuplicateVerifierProvider(), top_k))
    target = next(
        item for item in result.final_reviews if item.source_id == "CONFIG_FUNCTION_CODES"
    )
    assert target.status is FinalStatus.REJECTED_UNSUPPORTED
    assert target.verifier_reason == "Verifier returned duplicate verdicts"
    assert target.evidence is None


def test_engineering_review_provider_failure_exposes_no_advice() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, FailingReviewProvider(), top_k))
    assert all(
        item.status is FinalStatus.INSUFFICIENT_EVIDENCE
        for item in result.final_reviews
    )
    trace = next(item for item in result.role_traces if item.role == "engineering_review")
    assert trace.error == "RuntimeError: simulated provider outage"


def test_missing_reviewer_decisions_are_explicitly_blocked() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, IncompleteReviewProvider(), top_k))
    missing = [
        item
        for item in result.final_reviews
        if item.blocked_stage == "schema_missing_source"
    ]
    assert len(missing) == top_k - 1
    assert all(item.evidence is None for item in missing)


def test_duplicate_and_external_reviewer_decisions_are_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(
        run_case(case, retriever, DuplicateAndExternalReviewProvider(), top_k)
    )
    blocked_stages = {item.blocked_stage for item in result.final_reviews}
    assert "schema_duplicate_source" in blocked_stages
    assert "source_not_in_fixed_top_k" in blocked_stages
    assert all(
        item.evidence is None
        for item in result.final_reviews
        if item.blocked_stage in {"schema_duplicate_source", "source_not_in_fixed_top_k"}
    )
    duplicate_source = result.proposed_reviews[0].source_id
    assert not any(
        item.source_id == duplicate_source
        and item.status is FinalStatus.VERIFIED_REVIEW
        for item in result.final_reviews
    )


def test_missing_verifier_verdict_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, MissingVerifierProvider(), top_k))
    target = next(
        item for item in result.final_reviews if item.source_id == "CONFIG_FUNCTION_CODES"
    )
    assert target.status is FinalStatus.REJECTED_UNSUPPORTED
    assert target.blocked_stage == "independent_verifier"
    assert target.verifier_reason == "Verifier returned no verdict"
    assert target.evidence is None


def test_change_analyst_timeout_fails_before_retrieval() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    with pytest.raises(TimeoutError):
        asyncio.run(
            run_case(
                case,
                retriever,
                SlowAnalystProvider(),
                top_k,
                role_timeout_seconds=0.001,
            )
        )
