"""End-to-end smoke test — hits the real Anthropic API.

Requires ANTHROPIC_API_KEY in env. Uses claude-haiku-4-5 to keep cost ~$0.001.
"""
from __future__ import annotations

import asyncio
import json
import os

from uce_core import load_competency_from_dict
from uce_llm.registry import build_provider
from uce_runtime import CompetencyExecutor

print("ANTHROPIC_API_KEY present:", bool(os.environ.get("ANTHROPIC_API_KEY")))

DEFINITION = {
    "id": "smoke",
    "name": "Smoke Test",
    "mission": "Verify UCE end-to-end against the real Anthropic API",
    "objectives": [{"id": "verify", "name": "Verify end-to-end execution"}],
    "skills": [
        {
            "id": "echo_haiku",
            "name": "Echo Haiku",
            "execution_steps": [
                {
                    "id": "write",
                    "type": "prompt",
                    "prompt": "Write a one-line haiku-style summary (3 short phrases separated by /) about the topic: {{ inputs.topic }}",
                    "output_key": "haiku",
                }
            ],
        }
    ],
    "workflows": [
        {
            "id": "main",
            "name": "Main",
            "is_default": True,
            "steps": [{"id": "do", "type": "skill", "skill": "echo_haiku", "output_key": "haiku"}],
        }
    ],
    "policies": [{"id": "allow", "name": "Allow", "effect": "allow", "applies_to": ["*"]}],
    "llm": {
        "provider": "anthropic",
        "model": "claude-haiku-4-5",
        "temperature": 0.5,
        "max_tokens": 256,
    },
}


async def main() -> int:
    competency = load_competency_from_dict(DEFINITION)
    llm = build_provider(
        provider=competency.llm.provider,
        model=competency.llm.model,
        temperature=competency.llm.temperature,
        max_tokens=competency.llm.max_tokens,
    )
    executor = CompetencyExecutor(competency=competency, llm=llm)
    ctx, plan, ev = await executor.execute(
        {"topic": "competencies vs skills in AI systems"}, run_plan=False
    )
    print("STATUS:", ctx.status.value)
    print("OUTPUT:", ctx.outputs.get("haiku"))
    print(f"TOKENS in/out/cost: {ctx.usage.prompt_tokens} / {ctx.usage.completion_tokens} / ${ctx.usage.cost_usd:.4f}")
    print("EVAL:", json.dumps(ev.to_dict(), default=str))
    if ctx.error:
        print("ERROR:", ctx.error)
    # Print first error event from audit
    from uce_runtime.audit import InMemorySink
    sink = executor.audit.first_sink()
    if hasattr(sink, "events"):
        for e in sink.events:
            if e.error:
                print(f"AUDIT_ERR: {e.event_type} action={e.action} error={e.error}")
    return 0 if ctx.status.value == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
