"""Ollama provider adapter (HTTP, no SDK dependency)."""
from __future__ import annotations

from typing import Any

import httpx

from uce_llm.base import LLMError, LLMProvider, Message, Response, Role, TokenUsage


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = self.base_url or "http://localhost:11434"

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
        ollama_messages: list[dict[str, Any]] = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        for m in messages:
            role = m.role.value if m.role != Role.TOOL else "user"
            ollama_messages.append({"role": role, "content": m.content})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        if stop:
            payload["options"]["stop"] = stop

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as e:
            raise LLMError(f"Ollama HTTP error: {e}") from e

        text = (data.get("message") or {}).get("content", "")
        in_tok = int(data.get("prompt_eval_count") or 0)
        out_tok = int(data.get("eval_count") or 0)
        usage = TokenUsage(
            prompt_tokens=in_tok,
            completion_tokens=out_tok,
            total_tokens=in_tok + out_tok,
            cost_usd=0.0,  # local
        )
        return Response(
            text=text,
            model=self.model,
            provider=self.name,
            usage=usage,
            stop_reason=data.get("done_reason"),
            raw={"model": data.get("model")},
        )
