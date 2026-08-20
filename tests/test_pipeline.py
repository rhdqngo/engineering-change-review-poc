import asyncio

from ecr_poc.data import load_cases
from ecr_poc.models import (
    CandidateDecision,
    CandidateDecisionBatch,
    CandidateFinalStatus,
    ClaimVerification,
    ClaimVerificationBatch,
    Decision,
    OverallReviewStatus,
    VerifierVerdict,
)
from ecr_poc.pipeline import run_case
from ecr_poc.providers import FixtureProvider
from ecr_poc.web import _live_runtime


def setup_case(case_id: str):
    _, top_k, cases = load_cases()
    case = next(item for item in cases if item.id == case_id)
    return case, top_k, _live_runtime().retriever


def test_broad_expanded_and_final_docket_are_sealed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, FixtureProvider(), top_k))
    assert result.retrieval is not None
    assert result.query_processing is not None
    assert result.retrieval.broad_count == 40
    assert result.retrieval.expanded_count <= 200
    assert len(result.candidates) == 10
    assert result.candidate_fingerprint == result.retrieval.final_docket_fingerprint
    assert result.broad_candidate_source_ids[:10] != result.proposed_candidate_source_ids
    assert any(
        item.source_id in case.expected_review_targets
        and item.status is CandidateFinalStatus.VERIFIED_REVIEW
        for item in result.candidate_results
    )


def test_all_20_cases_have_deterministic_final_sequence_and_fingerprints() -> None:
    _, top_k, cases = load_cases()
    retriever = _live_runtime().retriever
    first = [
        asyncio.run(run_case(case, retriever, FixtureProvider(), top_k))
        for case in cases
    ]
    second = [
        asyncio.run(run_case(case, retriever, FixtureProvider(), top_k))
        for case in cases
    ]
    assert len(first) == 20
    for left, right in zip(first, second):
        assert left.broad_candidate_source_ids == right.broad_candidate_source_ids
        assert left.expanded_candidate_source_ids == right.expanded_candidate_source_ids
        assert left.candidate_fingerprint == right.candidate_fingerprint
        assert left.embedding_index_fingerprint == retriever.embedding_index_fingerprint
        assert left.identifier_index_fingerprint == retriever.identifier_index_fingerprint


def test_non_exact_claim_is_blocked_before_verifier_and_hidden() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(
        run_case(case, retriever, FixtureProvider(inject_unsupported=True), top_k)
    )
    blocked = [
        item
        for item in result.candidate_results
        if "deterministic_exact_span" in item.blocked_stages
    ]
    assert len(blocked) == 1
    assert blocked[0].status is CandidateFinalStatus.BLOCKED
    assert blocked[0].verified_claims == []
    public_projection = "".join(
        item.model_dump_json() for item in result.candidate_results
    )
    assert "THIS SPAN DOES NOT EXIST" not in public_projection
    assert result.overall_status is OverallReviewStatus.REVIEW_REQUIRED
    assert result.partial is True


class RejectingVerifierProvider(FixtureProvider):
    async def verify(self, case, claims):
        _, trace = await super().verify(case, claims)
        return ClaimVerificationBatch(
            verifications=[
                ClaimVerification(
                    claim_id=claim.claim_id,
                    verdict=VerifierVerdict.REJECTED,
                    reason="Evidence does not entail this claim.",
                )
                for claim in claims
            ]
        ), trace


class DuplicateVerifierProvider(FixtureProvider):
    async def verify(self, case, claims):
        _, trace = await super().verify(case, claims)
        claim = claims[0]
        return ClaimVerificationBatch(
            verifications=[
                ClaimVerification(
                    claim_id=claim.claim_id,
                    verdict=VerifierVerdict.SUPPORTED,
                    reason="First verdict.",
                ),
                ClaimVerification(
                    claim_id=claim.claim_id,
                    verdict=VerifierVerdict.SUPPORTED,
                    reason="Duplicate verdict.",
                ),
            ]
        ), trace


class FailingReviewProvider(FixtureProvider):
    async def review(self, case, candidates, final_docket_fingerprint):
        raise RuntimeError("simulated provider outage")


class IncompleteReviewProvider(FixtureProvider):
    async def review(self, case, candidates, final_docket_fingerprint):
        batch, trace = await super().review(
            case, candidates, final_docket_fingerprint
        )
        return CandidateDecisionBatch(decisions=batch.decisions[:1]), trace


class DuplicateAndExternalReviewProvider(FixtureProvider):
    async def review(self, case, candidates, final_docket_fingerprint):
        batch, trace = await super().review(
            case, candidates, final_docket_fingerprint
        )
        return CandidateDecisionBatch(
            decisions=[
                *batch.decisions,
                batch.decisions[0],
                CandidateDecision(
                    source_id="OUTSIDE_FINAL_DOCKET",
                    decision=Decision.NO_REVIEW,
                ),
            ]
        ), trace


class MissingVerifierProvider(FixtureProvider):
    async def verify(self, case, claims):
        _, trace = await super().verify(case, claims)
        return ClaimVerificationBatch(verifications=[]), trace


class SlowReviewerProvider(FixtureProvider):
    async def review(self, case, candidates, final_docket_fingerprint):
        await asyncio.sleep(0.05)
        return await super().review(case, candidates, final_docket_fingerprint)


class SlowVerifierProvider(FixtureProvider):
    async def verify(self, case, claims):
        await asyncio.sleep(0.05)
        return await super().verify(case, claims)


def test_independent_verifier_rejection_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, RejectingVerifierProvider(), top_k))
    target = next(
        item
        for item in result.candidate_results
        if item.source_id in case.expected_review_targets
    )
    assert target.status is CandidateFinalStatus.NO_SUPPORTED_CLAIM
    assert target.verified_claims == []
    assert result.overall_status is OverallReviewStatus.NO_SUPPORTED_REVIEW


def test_duplicate_verifier_verdict_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, DuplicateVerifierProvider(), top_k))
    target = next(
        item
        for item in result.candidate_results
        if item.source_id in case.expected_review_targets
    )
    assert target.status is CandidateFinalStatus.BLOCKED
    assert target.blocked_stages == ["verifier_duplicate_verdict"]
    assert target.verified_claims == []


def test_engineering_reviewer_failure_returns_inconclusive_without_advice() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, FailingReviewProvider(), top_k))
    assert all(
        item.status is CandidateFinalStatus.BLOCKED
        for item in result.candidate_results
    )
    assert all(not item.verified_claims for item in result.candidate_results)
    assert result.overall_status is OverallReviewStatus.INCONCLUSIVE
    trace = next(item for item in result.role_traces if item.role == "engineering_review")
    assert trace.error == "RuntimeError: simulated provider outage"


def test_missing_reviewer_decisions_are_explicitly_blocked() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, IncompleteReviewProvider(), top_k))
    missing = [
        item
        for item in result.candidate_results
        if "schema_missing_source" in item.blocked_stages
    ]
    assert len(missing) == top_k - 1
    assert all(not item.verified_claims for item in missing)


def test_duplicate_and_external_reviewer_decisions_are_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(
        run_case(case, retriever, DuplicateAndExternalReviewProvider(), top_k)
    )
    assert all(
        item.source_id != "OUTSIDE_FINAL_DOCKET"
        for item in result.candidate_results
    )
    duplicate = result.candidate_results[0]
    assert duplicate.status is CandidateFinalStatus.BLOCKED
    assert duplicate.blocked_stages == ["schema_duplicate_source"]
    assert result.partial is True


def test_missing_verifier_verdict_is_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    result = asyncio.run(run_case(case, retriever, MissingVerifierProvider(), top_k))
    target = next(
        item
        for item in result.candidate_results
        if item.source_id in case.expected_review_targets
    )
    assert target.status is CandidateFinalStatus.BLOCKED
    assert target.blocked_stages == ["verifier_missing_verdict"]
    assert target.verifier_verdicts == [VerifierVerdict.MISSING]
    assert target.verified_claims == []


def test_reviewer_and_verifier_timeouts_fail_closed() -> None:
    case, top_k, retriever = setup_case("DIR-01")
    reviewer = asyncio.run(
        run_case(
            case,
            retriever,
            SlowReviewerProvider(),
            top_k,
            role_timeout_seconds=0.001,
        )
    )
    assert reviewer.overall_status is OverallReviewStatus.INCONCLUSIVE
    assert not any(item.verified_claims for item in reviewer.candidate_results)

    verifier = asyncio.run(
        run_case(
            case,
            retriever,
            SlowVerifierProvider(),
            top_k,
            role_timeout_seconds=0.001,
        )
    )
    assert verifier.overall_status is OverallReviewStatus.INCONCLUSIVE
    assert not any(item.verified_claims for item in verifier.candidate_results)
