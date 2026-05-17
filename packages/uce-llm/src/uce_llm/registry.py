"""Provider registry — map provider name to implementation."""
from __future__ import annotations

from typing import Any

from uce_llm.base import LLMError, LLMProvider

_REGISTRY: dict[str, type[LLMProvider]] = {}


def register_provider(name: str, cls: type[LLMProvider]) -> None:
    """Register a provider class under a name. Overwrites silently."""
    _REGISTRY[name] = cls


def get_provider_class(name: str) -> type[LLMProvider]:
    if name not in _REGISTRY:
        raise LLMError(
            f"Unknown LLM provider '{name}'. Registered: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]


def build_provider(
    provider: str,
    *,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    extra: dict[str, Any] | None = None,
) -> LLMProvider:
    cls = get_provider_class(provider)
    return cls(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        extra=extra,
    )


# Auto-register built-in providers. Imports are local to keep registry import-light.
def _bootstrap_builtins() -> None:
    from uce_llm.anthropic import AnthropicProvider
    from uce_llm.ollama import OllamaProvider
    from uce_llm.openai import OpenAIProvider

    register_provider("anthropic", AnthropicProvider)
    register_provider("openai", OpenAIProvider)
    register_provider("ollama", OllamaProvider)


_bootstrap_builtins()
