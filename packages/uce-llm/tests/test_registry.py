from __future__ import annotations

import pytest

from uce_llm import LLMError, get_provider_class, register_provider
from uce_llm.base import LLMProvider, Response


class _Custom(LLMProvider):
    name = "custom"

    async def complete(self, messages, **kwargs):  # type: ignore[override]
        return Response(text="", model=self.model, provider=self.name)


def test_built_in_providers_registered():
    for name in ("anthropic", "openai", "ollama"):
        cls = get_provider_class(name)
        assert issubclass(cls, LLMProvider)


def test_register_and_lookup_custom():
    register_provider("custom", _Custom)
    assert get_provider_class("custom") is _Custom


def test_unknown_provider_raises():
    with pytest.raises(LLMError):
        get_provider_class("nonexistent-provider-xyz")
