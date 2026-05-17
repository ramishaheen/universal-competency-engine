"""Run the Procurement competency end-to-end via the Python SDK (no API needed).

Requires ANTHROPIC_API_KEY (or change competency.llm.provider).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from uce_core import load_competency
from uce_llm.registry import build_provider
from uce_runtime import CompetencyExecutor


async def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Export it or switch the competency's llm.provider.", file=sys.stderr)
        return 1

    competency = load_competency("competencies/procurement/competency.yaml")
    llm = build_provider(
        provider=competency.llm.provider,
        model=competency.llm.model,
        temperature=competency.llm.temperature,
        max_tokens=competency.llm.max_tokens,
    )
    executor = CompetencyExecutor(competency=competency, llm=llm)

    ctx, plan, evaluation = await executor.execute(
        inputs={
            "request": "Buy 25 4K monitors for the design team",
            "budget_usd": 12000,
            "deadline": "2026-06-30",
        },
        actor={"id": "rami", "roles": ["operator"]},
    )

    print("STATUS:", ctx.status.value)
    if plan:
        print(f"PLAN: confidence={plan.confidence:.2f} risk={plan.risk_score:.2f} alignment={plan.alignment_score:.2f}")
    print("\n=== OUTPUTS ===")
    print(json.dumps(ctx.outputs, indent=2, default=str))
    print("\n=== EVALUATION ===")
    print(json.dumps(evaluation.to_dict(), indent=2, default=str))
    return 0 if ctx.status.value == "succeeded" else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
