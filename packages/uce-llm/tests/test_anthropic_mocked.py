"""Mocked Anthropic adapter tests (no real API calls)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from uce_llm.anthropic import AnthropicProvider
from uce_llm.base import Message, Role


@pytest.fixture
def fake_anthropic_response():
    return SimpleNamespace(
        id="msg_1",
        content=[SimpleNamespace(type="text", text="Hello back!")],
        usage=SimpleNamespace(input_tokens=10, output_tokens=4),
        stop_reason="end_turn",
    )


@pytest.mark.asyncio
async def test_anthropic_complete_translates_messages_and_usage(monkeypatch, fake_anthropic_response):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    p = AnthropicProvider(model="claude-sonnet-4-6")
    p._client.messages.create = AsyncMock(return_value=fake_anthropic_response)  # type: ignore[attr-defined]
    r = await p.complete(
        [Message(role=Role.USER, content="Hello")],
        system="You are helpful",
    )
    assert r.text == "Hello back!"
    assert r.provider == "anthropic"
    assert r.usage.prompt_tokens == 10
    assert r.usage.completion_tokens == 4
    assert r.usage.cost_usd > 0  # priced model
    # Verify the SDK was called with system extracted and only user/assistant in messages
    call_kwargs = p._client.messages.create.call_args.kwargs  # type: ignore[attr-defined]
    assert call_kwargs["system"] == [{"type": "text", "text": "You are helpful"}]
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]


@pytest.mark.asyncio
async def test_anthropic_folds_system_messages(monkeypatch, fake_anthropic_response):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    p = AnthropicProvider(model="claude-sonnet-4-6")
    p._client.messages.create = AsyncMock(return_value=fake_anthropic_response)  # type: ignore[attr-defined]
    await p.complete(
        [
            Message(role=Role.SYSTEM, content="rule 1"),
            Message(role=Role.SYSTEM, content="rule 2"),
            Message(role=Role.USER, content="hi"),
        ],
        system="top-level system",
    )
    call_kwargs = p._client.messages.create.call_args.kwargs  # type: ignore[attr-defined]
    sys_text = call_kwargs["system"][0]["text"]
    assert "top-level system" in sys_text
    assert "rule 1" in sys_text
    assert "rule 2" in sys_text
    assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_anthropic_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from uce_llm.base import LLMError

    with pytest.raises(LLMError):
        AnthropicProvider(model="claude-sonnet-4-6")
