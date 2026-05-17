"""Provider-agnostic LLM interface.

All providers (Anthropic, OpenAI, Ollama, custom) implement `LLMProvider`.
The interface is intentionally small so adding a new provider stays under ~100 LOC.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class Response:
    text: str
    model: str
    provider: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    stop_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    text: str
    is_final: bool = False
    usage: TokenUsage | None = None


class LLMError(RuntimeError):
    """Wraps any provider error in a consistent type."""


class LLMProvider(ABC):
    """Abstract LLM provider. Subclasses implement `complete` (and optionally `stream`)."""

    name: str = "abstract"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra = extra or {}

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> Response:
        """Synchronous completion (returns when full text is available)."""

    async def stream(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Streaming completion. Default falls back to non-streaming."""
        resp = await self.complete(
            messages, system=system, temperature=temperature, max_tokens=max_tokens
        )
        yield StreamChunk(text=resp.text, is_final=True, usage=resp.usage)

    # Convenience
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{self.__class__.__name__} model={self.model!r}>"
