import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ecr_poc.evaluation import evaluate
from ecr_poc.models import EvaluationRun
from ecr_poc.storage import StoredObject, validate_historical_runs


class CheckpointFailingStore:
    kind = "test"
    location = "test://checkpoint-failure"

    def __init__(self) -> None:
        self.failure: dict[str, Any] | None = None
        self.final_written = False

    def write_checkpoint(self, payload: dict[str, Any]) -> StoredObject:
        raise PermissionError("simulated checkpoint denial")

    def write_failure(self, payload: dict[str, Any]) -> StoredObject:
        self.failure = payload
        return StoredObject("test://failure.json", 1, "failure")

    def write_final(self, run: EvaluationRun) -> StoredObject:
        self.final_written = True
        return StoredObject("test://evaluation.json", 1, "evaluation")


def test_fixture_evaluation_metrics() -> None:
    output = (Path.cwd() / ".runtime/test-evaluation-v6.json").resolve()
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=output,
            experiment_manifest="ecr-poc-v6.json",
            source_commit="LOCAL-V6-FUNCTIONAL-GATE",
            inject_unsupported=True,
            update_latest=False,
        )
    )
    assert len(run.cases) == 20
    assert run.experiment_id == "ecr-poc-regression-v6"
    assert run.metrics["overall"]["final_docket_hit_at_10"]["eligible_targets"] == 16
    assert run.metrics["overall"]["clean_benign_false_alarm"]["cases"] == 0
    assert run.metrics["overall"]["claim_counts"]["blocked"] == 1
    assert run.metrics["overall"]["selection"]["average_final_docket_size"] == 10
    assert run.provenance is not None
    assert run.provenance.identifier_index_fingerprint == run.configuration[
        "identifier_index_fingerprint"
    ]
    checkpoint = json.loads(
        output.with_suffix(".checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["status"] == "complete"
    assert checkpoint["completed_case_ids"] == [item.case_id for item in run.cases]


def test_v1_through_v5_are_read_only_offline_compatible() -> None:
    validated = validate_historical_runs()
    assert set(validated) == {"v1", "v2", "v3", "v4", "v5", "v5-q1"}


def test_evaluation_refuses_to_overwrite_historical_result_paths() -> None:
    with pytest.raises(RuntimeError, match="immutable v1-v5 historical result"):
        asyncio.run(
            evaluate(
                provider_name="fixture",
                embedding_provider="local",
                output_path=Path("results/runs/vertex-adk-v4.json"),
                update_latest=False,
            )
        )


def test_checkpoint_failure_records_failure_and_never_writes_final() -> None:
    store = CheckpointFailingStore()
    with pytest.raises(PermissionError, match="simulated checkpoint denial"):
        asyncio.run(
            evaluate(
                provider_name="fixture",
                embedding_provider="local",
                run_store=store,
                run_id="checkpoint-failure-run",
            )
        )
    assert store.failure is not None
    assert store.failure["blocked_stage"] == "checkpoint_write"
    assert store.final_written is False
