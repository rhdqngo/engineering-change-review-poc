from ecr_poc.data import load_artifacts, load_cases, validate_all
from ecr_poc.retrieval import DeterministicHashEmbedder, HybridRetriever


def test_frozen_data_integrity_and_distribution() -> None:
    assert validate_all() == {
        "artifacts": 32,
        "cases": 18,
        "direct": 4,
        "semantic": 4,
        "cross_artifact": 4,
        "clean": 3,
        "benign": 3,
    }


def test_offline_retrieval_covers_every_frozen_mutation_target() -> None:
    _, top_k, cases = load_cases()
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    for case in cases:
        candidates = retriever.retrieve(case.change, top_k)
        candidate_ids = {candidate.source_id for candidate in candidates}
        if case.expected_review_targets:
            assert set(case.expected_review_targets).issubset(candidate_ids), case.id


def test_retrieval_is_deterministic() -> None:
    _, top_k, cases = load_cases()
    retriever = HybridRetriever(load_artifacts(), DeterministicHashEmbedder())
    first = retriever.retrieve(cases[0].change, top_k)
    second = retriever.retrieve(cases[0].change, top_k)
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
