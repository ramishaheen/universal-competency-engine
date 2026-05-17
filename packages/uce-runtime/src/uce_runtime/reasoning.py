"""Reasoner — produces a structured Plan from goal + context using an LLM.

The reasoner thinks BEFORE acting: it considers objectives, policies, memory,
risk, and confidence. It does NOT execute the plan — the WorkflowEngine /
SkillExecutor does that. This separation lets us:
- Cache plans (hash(goal+context) → Plan if confidence > threshold)
- Audit reasoning independently
- Swap reasoning strategies (CoT, plan-and-execute, ReAct) without touching execution
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from uce_core.models import Competency
from uce_llm.base import LLMProvider, Message, Role


@dataclass
class PlanStep:
    description: str
    skill_id: str | None = None  # if the step maps to a skill
    rationale: str = ""
    expected_output: str = ""


@dataclass
class Plan:
    goal: str
    rationale: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    risk_score: float = 0.5  # 0..1
    confidence: float = 0.5
    alignment_score: float = 0.5
    requires_human_approval: bool = False
    notes: list[str] = field(default_factory=list)
    raw_response: str = ""


class Reasoner:
    """Plan-builder. Uses the LLM to think through the goal, then returns a structured Plan."""

    SYSTEM = (
        "You are the reasoning layer of a Competency Engine. "
        "Given a goal, the competency definition, available skills, and relevant memory, "
        "produce a structured execution plan. Think about objectives, risks, prerequisites, "
        "and whether human approval is needed."
    )

    def __init__(self, *, competency: Competency, llm: LLMProvider) -> None:
        self.competency = competency
        self.llm = llm

    async def plan(
        self,
        goal: str,
        *,
        memory_snippets: list[str] | None = None,
        actor: dict[str, Any] | None = None,
    ) -> Plan:
        prompt = self._build_prompt(goal=goal, memory_snippets=memory_snippets or [], actor=actor or {})
        resp = await self.llm.complete(
            [Message(role=Role.USER, content=prompt)],
            system=self.SYSTEM,
        )
        plan = self._parse(resp.text, goal=goal)
        plan.raw_response = resp.text
        return plan

    def _build_prompt(self, *, goal: str, memory_snippets: list[str], actor: dict[str, Any]) -> str:
        skills_summary = "\n".join(
            f"  - {s.id}: {s.name} — {s.description or '(no description)'}"
            for s in self.competency.skills
        ) or "  (no skills defined)"
        objectives = "\n".join(f"  - {o.id}: {o.name}" for o in self.competency.objectives) or "  (none)"
        memory = "\n".join(f"  - {m}" for m in memory_snippets[:10]) or "  (none)"
        return (
            f"COMPETENCY: {self.competency.name} ({self.competency.id})\n"
            f"MISSION: {self.competency.mission or '(unspecified)'}\n"
            f"DOMAIN: {self.competency.domain or '(unspecified)'}\n"
            f"RISK LEVEL: {self.competency.risk_level.value}\n"
            f"OBJECTIVES:\n{objectives}\n\n"
            f"AVAILABLE SKILLS:\n{skills_summary}\n\n"
            f"RELEVANT MEMORY:\n{memory}\n\n"
            f"ACTOR: {json.dumps(actor)}\n\n"
            f"GOAL: {goal}\n\n"
            "Respond with a JSON object only, no prose, in this exact shape:\n"
            "{\n"
            '  "rationale": "...",\n'
            '  "steps": [{"description": "...", "skill_id": "<existing skill id or null>", "rationale": "...", "expected_output": "..."}],\n'
            '  "risk_score": 0.0..1.0,\n'
            '  "confidence": 0.0..1.0,\n'
            '  "alignment_score": 0.0..1.0,\n'
            '  "requires_human_approval": true|false,\n'
            '  "notes": ["..."]\n'
            "}\n"
        )

    def _parse(self, text: str, *, goal: str) -> Plan:
        data = _extract_json_object(text)
        if data is None:
            # Fall back to a one-step plan that captures the raw rationale, so execution can continue.
            return Plan(
                goal=goal,
                rationale=text.strip()[:500],
                steps=[],
                confidence=0.3,
                notes=["plan parser fell back to free-text mode"],
            )
        steps_raw = data.get("steps") or []
        steps = [
            PlanStep(
                description=str(s.get("description", "")),
                skill_id=(s.get("skill_id") or None),
                rationale=str(s.get("rationale", "")),
                expected_output=str(s.get("expected_output", "")),
            )
            for s in steps_raw
            if isinstance(s, dict)
        ]
        return Plan(
            goal=goal,
            rationale=str(data.get("rationale", "")),
            steps=steps,
            risk_score=_clamp(data.get("risk_score", 0.5)),
            confidence=_clamp(data.get("confidence", 0.5)),
            alignment_score=_clamp(data.get("alignment_score", 0.5)),
            requires_human_approval=bool(data.get("requires_human_approval", False)),
            notes=[str(n) for n in (data.get("notes") or [])],
        )


def _clamp(v: Any) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, f))


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Find the first top-level JSON object in `text`, tolerating prose around it."""
    # Strip common code fences first.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fenced:
        candidate = fenced.group(1)
    else:
        # Greedy match the outermost {...}
        match = re.search(r"\{.*\}", text, flags=re.S)
        candidate = match.group(0) if match else None
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None
