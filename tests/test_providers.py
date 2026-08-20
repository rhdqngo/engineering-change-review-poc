import asyncio
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import ClassVar

import pytest
from google.adk.events import Event
from google.genai import types

from ecr_poc.adk_agent.agent import GENERATION, engineering_review_agent
from ecr_poc.models import CandidateDecisionBatch
from ecr_poc.providers import AdkVertexProvider


class FakeSessionService:
    async def create_session(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(id="test-session")


class FakeRunner:
    events: ClassVar[list[Event]] = []

    def __init__(self, *, agent: object, app_name: str) -> None:
        del agent
        self.app_name = app_name
        self.session_service = FakeSessionService()

    async def run_async(self, **_: object) -> AsyncGenerator[Event]:
        for event in self.events:
            yield event


def final_event(text: str, finish_reason: types.FinishReason) -> Event:
    return Event(
        author="engineering_review",
        content=types.ModelContent(parts=[types.Part(text=text)]),
        finish_reason=finish_reason,
        partial=False,
    )


def test_generation_budget_uses_model_supported_maximum() -> None:
    assert GENERATION.max_output_tokens == 65_536


def test_provider_accepts_one_naturally_completed_final_event(monkeypatch) -> None:
    monkeypatch.setattr("ecr_poc.providers.InMemoryRunner", FakeRunner)
    FakeRunner.events = [
        final_event('{"decisions": []}', types.FinishReason.STOP),
    ]

    parsed, raw = asyncio.run(
        AdkVertexProvider()._run(
            engineering_review_agent,
            "untrusted prompt",
            CandidateDecisionBatch,
        )
    )

    assert parsed.decisions == []
    assert raw == '{"decisions": []}'


def test_provider_blocks_truncated_max_tokens_event(monkeypatch) -> None:
    monkeypatch.setattr("ecr_poc.providers.InMemoryRunner", FakeRunner)
    FakeRunner.events = [
        final_event('{"decisions": [', types.FinishReason.MAX_TOKENS),
    ]

    with pytest.raises(RuntimeError, match="stopped before completion: MAX_TOKENS"):
        asyncio.run(
            AdkVertexProvider()._run(
                engineering_review_agent,
                "untrusted prompt",
                CandidateDecisionBatch,
            )
        )


def test_provider_ignores_partial_and_requires_exactly_one_final_output(
    monkeypatch,
) -> None:
    monkeypatch.setattr("ecr_poc.providers.InMemoryRunner", FakeRunner)
    FakeRunner.events = [
        Event(
            author="engineering_review",
            content=types.ModelContent(parts=[types.Part(text='{"decisions":')]),
            partial=True,
        ),
    ]

    with pytest.raises(RuntimeError, match="returned 0 final structured outputs"):
        asyncio.run(
            AdkVertexProvider()._run(
                engineering_review_agent,
                "untrusted prompt",
                CandidateDecisionBatch,
            )
        )
