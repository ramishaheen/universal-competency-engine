"""Anthropic Claude provider adapter."""
from __future__ import annotations

import os
from typing import Any

from uce_llm.base import LLMError, LLMProvider, Message, Response, Role, TokenUsage


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    # Rough per-1K-token rates for cost estimation (input/output, USD). Override as needed.
    _PRICES: dict[str, tuple[float, float]] = {
        "claude-opus-4-7": (15.0, 75.0),
        "claude-opus-4-6": (15.0, 75.0),
        "claude-sonnet-4-6": (3.0, 15.0),
        "claude-sonnet-4-5": (3.0, 15.0),
        "claude-haiku-4-5": (0.8, 4.0),
        "claude-3-5-sonnet-20241022": (3.0, 15.0),
        "claude-3-5-haiku-20241022": (0.8, 4.0),
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY not set and no api_key provided")
        # Lazy import keeps adapter usable in environments without the SDK
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key, base_url=self.base_url)

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
        # Anthropic API separates `system` from message list, and only allows user/assistant roles.
        anthropic_messages: list[dict[str, Any]] = []
        derived_system: list[str] = [system] if system else []
        for m in messages:
            if m.role == Role.SYSTEM:
                derived_system.append(m.content)
            else:
                # tool messages are folded in as user content with a label, since we don't
                # use Claude's native tool-use here (the runtime orchestrates tools itself).
                content = m.content if m.role != Role.TOOL else f"[tool {m.name or ''}] {m.content}"
                role = "user" if m.role in (Role.USER, Role.TOOL) else "assistant"
                anthropic_messages.append({"role": role, "content": content})

        # Anthropic API: `system` is either omitted or an array of text blocks.
        system_text = "\n\n".join(s for s in derived_system if s)
        system_kwarg: list[dict[str, str]] | None = (
            [{"type": "text", "text": system_text}] if system_text else None
        )
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if system_kwarg is not None:
            kwargs["system"] = system_kwarg
        if stop:
            kwargs["stop_sequences"] = stop
        try:
            api_resp = await self._client.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001 — re-raised as LLMError
            raise LLMError(f"Anthropic API error: {e}") from e

        text = "".join(block.text for block in api_resp.content if getattr(block, "type", "") == "text")
        usage = self._extract_usage(api_resp)
        return Response(
            text=text,
            model=self.model,
            provider=self.name,
            usage=usage,
            stop_reason=getattr(api_resp, "stop_reason", None),
            raw={"id": getattr(api_resp, "id", None)},
        )

    def _extract_usage(self, api_resp: Any) -> TokenUsage:
        u = getattr(api_resp, "usage", None)
        if u is None:
            return TokenUsage()
        in_tok = getattr(u, "input_tokens", 0) or 0
        out_tok = getattr(u, "output_tokens", 0) or 0
        # Prices are USD per 1M tokens.
        in_price, out_price = self._PRICES.get(self.model, (0.0, 0.0))
        cost = (in_tok / 1_000_000) * in_price + (out_tok / 1_000_000) * out_price
        return TokenUsage(
            prompt_tokens=in_tok,
            completion_tokens=out_tok,
            total_tokens=in_tok + out_tok,
            cost_usd=round(cost, 6),
        )
