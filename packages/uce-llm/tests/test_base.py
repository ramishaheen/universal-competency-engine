from __future__ import annotations

import pytest

from uce_llm.base import LLMProvider, Message, Response, Role, TokenUsage


class _FakeProvider(LLMProvider):
    name = "fake"

    async def complete(self, messages, **kwargs):  # type: ignore[override]
        return Response(
            text="hello " + messages[-1].content,
            model=self.model,
            provider=self.name,
            usage=TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        )


def test_message_as_dict_includes_extras():
    m = Message(role=Role.TOOL, content="x", name="t1", tool_call_id="call_1")
    d = m.as_dict()
    assert d == {"role": "tool", "content": "x", "name": "t1", "tool_call_id": "call_1"}


@pytest.mark.asyncio
async def test_fake_provider_completes():
    p = _FakeProvider(model="m1")
    r = await p.complete([Message(role=Role.USER, content="world")])
    assert r.text == "hello world"
    assert r.usage.total_tokens == 3
    assert r.provider == "fake"


@pytest.mark.asyncio
async def test_default_stream_yields_single_chunk():
    p = _FakeProvider(model="m1")
    chunks = []
    async for c in p.stream([Message(role=Role.USER, content="x")]):
        chunks.append(c)
    assert len(chunks) == 1
    assert chunks[0].is_final is True
