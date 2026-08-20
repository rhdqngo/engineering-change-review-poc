import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ecr_poc.evaluation import evaluate
from ecr_poc.models import EvaluationRun
from ecr_poc.storage import StoredObject


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
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-evaluation.json"),
            inject_unsupported=True,
            update_latest=False,
        )
    )
    assert run.metrics["overall"]["retrieval_coverage"] == {
        "hits": 12,
        "eligible": 12,
        "rate": 1.0,
    }
    assert run.metrics["overall"]["llm_review_success"]["successes"] == 12
    assert run.metrics["overall"]["false_alarm"]["cases"] == 0
    assert run.metrics["overall"]["unsupported_output_blocked"] == 1
    checkpoint = json.loads(
        Path(".runtime/test-evaluation.checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["status"] == "complete"
    assert checkpoint["completed_case_ids"] == [item.case_id for item in run.cases]


def test_v2_fixture_run_records_reproducible_provenance() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-evaluation-v2.json"),
            experiment_manifest="ecr-poc-v2.json",
            run_id="test-v2-run",
            source_commit="0123456789abcdef",
            update_latest=False,
        )
    )
    assert run.experiment_id == "ecr-poc-preregistered-v2"
    assert run.run_id == "test-v2-run"
    assert run.provenance is not None
    assert run.provenance.freeze_tag == "ecr-poc-v2-freeze"
    assert run.provenance.experiment_manifest == "ecr-poc-v2.json"
    assert run.provenance.source_commit == "0123456789abcdef"
    assert run.provenance.prompt_version == "ecr-poc-prompts-v2"
    assert run.provenance.prompt_hashes == {
        "change_analyst": "5a840bea138ff965ea727e5498401d573cb563c75f978b3e27a6ab8bdfecac1f",
        "engineering_review": "d014f104f679b742153b8746059d7584c21f561b98ce494a4763ad10e3733e9b",
        "evidence_verifier": "9e6057d53ad3ebe7bf68754cf06f50918c862522cb91a952e935eb3afe3a21a6",
    }
    assert all(case.run_id == "test-v2-run" for case in run.cases)


def test_v3_fixture_run_records_manifest_and_unchanged_prompts() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-evaluation-v3.json"),
            experiment_manifest="ecr-poc-v3.json",
            run_id="test-v3-run",
            source_commit="fedcba9876543210",
            update_latest=False,
        )
    )
    assert run.experiment_id == "ecr-poc-preregistered-v3"
    assert run.provenance is not None
    assert run.provenance.freeze_tag == "ecr-poc-v3-freeze"
    assert run.provenance.experiment_manifest == "ecr-poc-v3.json"
    assert run.provenance.prompt_version == "ecr-poc-prompts-v2"
    assert all(case.run_id == "test-v3-run" for case in run.cases)


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
