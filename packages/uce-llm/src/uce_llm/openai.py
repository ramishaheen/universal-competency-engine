"""OpenAI provider adapter."""
from __future__ import annotations

import os
from typing import Any

from uce_llm.base import LLMError, LLMProvider, Message, Response, TokenUsage


class OpenAIProvider(LLMProvider):
    name = "openai"

    _PRICES: dict[str, tuple[float, float]] = {
        "gpt-5": (5.0, 15.0),
        "gpt-5-mini": (0.5, 2.0),
        "gpt-4o": (2.5, 10.0),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4.1": (2.5, 10.0),
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY not set and no api_key provided")
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)

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
        oai_messages: list[dict[str, Any]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        for m in messages:
            oai_messages.append(m.as_dict())

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": oai_messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if stop:
            kwargs["stop"] = stop
        if response_format:
            kwargs["response_format"] = response_format

        try:
            api_resp = await self._client.chat.completions.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"OpenAI API error: {e}") from e

        choice = api_resp.choices[0]
        text = choice.message.content or ""
        usage = self._extract_usage(api_resp)
        return Response(
            text=text,
            model=self.model,
            provider=self.name,
            usage=usage,
            stop_reason=getattr(choice, "finish_reason", None),
            raw={"id": getattr(api_resp, "id", None)},
        )

    def _extract_usage(self, api_resp: Any) -> TokenUsage:
        u = getattr(api_resp, "usage", None)
        if u is None:
            return TokenUsage()
        in_tok = getattr(u, "prompt_tokens", 0) or 0
        out_tok = getattr(u, "completion_tokens", 0) or 0
        # Prices are USD per 1M tokens.
        in_price, out_price = self._PRICES.get(self.model, (0.0, 0.0))
        cost = (in_tok / 1_000_000) * in_price + (out_tok / 1_000_000) * out_price
        return TokenUsage(
            prompt_tokens=in_tok,
            completion_tokens=out_tok,
            total_tokens=in_tok + out_tok,
            cost_usd=round(cost, 6),
        )
