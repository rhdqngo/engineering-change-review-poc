from ecr_poc.data import repository_root
from ecr_poc.quality import compare_runs


def test_frozen_v5_q1_comparison_is_single_variable_and_case_classified() -> None:
    root = repository_root()
    comparison = compare_runs(
        root / "results/runs/fixture-v5-baseline.json",
        root / "results/runs/fixture-v5-q1.json",
    )
    assert all(comparison["invariant_checks"].values())
    assert comparison["baseline"]["query_version"] == "structured-change-v1"
    assert comparison["variant"]["query_version"] == (
        "structured-change-v2-artifact-delta"
    )
    assert comparison["delta"]["mean_rank"] < 0
    assert comparison["delta"]["mean_reciprocal_rank"] > 0
    assert len(comparison["cases"]) == 18
    for case in comparison["cases"]:
        for arm in ("baseline_failures", "variant_failures"):
            assert set(case[arm]) == {
                "retrieval_miss",
                "expected_target_miss",
                "mutation_unnecessary_warnings",
                "control_false_alarm",
                "verifier_pass_error",
            }
