import asyncio
import json
from pathlib import Path

from ecr_poc.evaluation import evaluate


def test_fixture_evaluation_metrics() -> None:
    run = asyncio.run(
        evaluate(
            provider_name="fixture",
            embedding_provider="local",
            output_path=Path(".runtime/test-evaluation.json"),
            inject_unsupported=True,
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
