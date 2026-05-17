"""Shared fixtures: a fake LLM so runtime tests never hit a network."""
from __future__ import annotations

from collections.abc import Callable

import pytest

from uce_llm.base import LLMProvider, Message, Response, TokenUsage


class FakeLLM(LLMProvider):
    """Deterministic LLM stub used across runtime tests."""

    name = "fake"

    def __init__(self, *, model: str = "fake-1", reply_fn: Callable[[list[Message], str | None], str] | None = None) -> None:
        super().__init__(model=model)
        self.calls: list[tuple[list[Message], str | None]] = []
        self.reply_fn = reply_fn or (lambda msgs, sys: f"echo: {msgs[-1].content if msgs else ''}")

    async def complete(self, messages, *, system=None, **kwargs):  # type: ignore[override]
        self.calls.append((list(messages), system))
        text = self.reply_fn(list(messages), system)
        return Response(
            text=text,
            model=self.model,
            provider=self.name,
            usage=TokenUsage(prompt_tokens=5, completion_tokens=10, total_tokens=15, cost_usd=0.0001),
        )


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_llm_factory():
    def make(reply_fn=None) -> FakeLLM:
        return FakeLLM(reply_fn=reply_fn)

    return make
