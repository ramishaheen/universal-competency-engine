"""Top-level competency executor — orchestrates the full execution flow.

Mirrors the user spec section 9:

    Request → load competency → retrieve memory → policy check → reason & plan
    → run workflow → validate → governance review → respond → memory update
    → audit log → evaluate
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from uce_core.models import Competency, MemoryType
from uce_llm.base import LLMProvider

from uce_runtime.audit import AuditLogger
from uce_runtime.context import RunContext, RunStatus
from uce_runtime.errors import PolicyDenied, PolicyRequiresApproval
from uce_runtime.evaluation import EvaluationResult, Evaluator
from uce_runtime.memory import MemoryStore
from uce_runtime.policy import PolicyEngine, PolicyEffect
from uce_runtime.reasoning import Plan, Reasoner
from uce_runtime.skills import SkillExecutor, ToolRegistry, register_builtin_tools
from uce_runtime.workflow import WorkflowEngine


class CompetencyExecutor:
    def __init__(
        self,
        *,
        competency: Competency,
        llm: LLMProvider,
        memory: MemoryStore | None = None,
        tools: ToolRegistry | None = None,
        audit: AuditLogger | None = None,
        default_policy_effect: PolicyEffect = PolicyEffect.ALLOW,
    ) -> None:
        self.competency = competency
        self.llm = llm
        self.memory = memory or MemoryStore()
        self.tools = tools or ToolRegistry()
        if not self.tools.has("http_get"):
            register_builtin_tools(self.tools)
        self.audit = audit or AuditLogger()
        self.policy = PolicyEngine(competency.policies, default_effect=default_policy_effect)
        self.reasoner = Reasoner(competency=competency, llm=llm)
        self.skill_executor = SkillExecutor(competency=competency, llm=llm, tools=self.tools)
        self.workflow_engine = WorkflowEngine(
            skill_executor=self.skill_executor,
            policy=self.policy,
            audit=self.audit,
        )
        self.evaluator = Evaluator()

    async def execute(
        self,
        inputs: dict[str, Any] | None = None,
        *,
        actor: dict[str, Any] | None = None,
        workflow_id: str | None = None,
        goal: str | None = None,
        run_plan: bool = True,
    ) -> tuple[RunContext, Plan | None, EvaluationResult]:
        ctx = RunContext(
            competency=self.competency,
            inputs=inputs or {},
            actor=actor or {"id": "anonymous", "roles": ["operator"]},
        )
        ctx.status = RunStatus.RUNNING
        start = time.monotonic()
        self.audit.emit(
            run_id=ctx.run_id,
            event_type="run.start",
            actor=ctx.actor,
            action=f"competency:{self.competency.id}:execute",
            inputs=ctx.inputs,
        )

        # Top-level policy gate
        gate_action = f"competency:{self.competency.id}:execute"
        gate = self.policy.check(gate_action, ctx.eval_context())
        self.audit.emit(
            run_id=ctx.run_id,
            event_type="policy.check",
            actor=ctx.actor,
            action=gate_action,
            decision=gate.effect.value,
            reasons=gate.reasons,
        )
        if gate.denied:
            ctx.status = RunStatus.DENIED
            ctx.error = "denied by policy: " + "; ".join(gate.reasons)
            ctx.finished_at = datetime.now(timezone.utc)
            self.audit.emit(
                run_id=ctx.run_id,
                event_type="run.end",
                actor=ctx.actor,
                action=gate_action,
                error=ctx.error,
                latency_ms=int((time.monotonic() - start) * 1000),
            )
            return ctx, None, self._evaluate(ctx)
        if gate.needs_approval:
            ctx.status = RunStatus.PENDING_APPROVAL
            ctx.pending_approval = {
                "phase": "execute",
                "required_role": gate.required_role,
                "reasons": gate.reasons,
            }
            ctx.finished_at = datetime.now(timezone.utc)
            return ctx, None, self._evaluate(ctx)

        # Retrieve memory snippets relevant to the goal/input
        snippets = self._retrieve_memory(goal=goal, inputs=ctx.inputs)

        # Reason (build plan)
        plan: Plan | None = None
        if run_plan and self.competency.skills:
            plan = await self.reasoner.plan(
                goal=goal or _default_goal(ctx),
                memory_snippets=snippets,
                actor=ctx.actor,
            )
            ctx.add_usage_from_plan = True  # marker for tests; harmless
            self.audit.emit(
                run_id=ctx.run_id,
                event_type="reason.plan",
                actor=ctx.actor,
                action=f"competency:{self.competency.id}:plan",
                outputs={
                    "step_count": len(plan.steps),
                    "confidence": plan.confidence,
                    "risk_score": plan.risk_score,
                    "alignment_score": plan.alignment_score,
                    "requires_human_approval": plan.requires_human_approval,
                },
            )
            if plan.requires_human_approval:
                ctx.status = RunStatus.PENDING_APPROVAL
                ctx.pending_approval = {
                    "phase": "plan",
                    "required_role": "operator",
                    "reasons": ["plan flagged for human approval"],
                    "plan_rationale": plan.rationale,
                }
                ctx.finished_at = datetime.now(timezone.utc)
                return ctx, plan, self._evaluate(ctx)

        # Execute the workflow
        workflow = (
            self.competency.workflow_by_id(workflow_id) if workflow_id else self.competency.default_workflow()
        )
        if workflow is not None:
            try:
                await self.workflow_engine.run(workflow, ctx)
            except PolicyDenied as e:
                ctx.status = RunStatus.DENIED
                ctx.error = str(e)
            except PolicyRequiresApproval as e:
                ctx.status = RunStatus.PENDING_APPROVAL
                ctx.pending_approval = {
                    "phase": "workflow",
                    "required_role": e.required_role,
                    "reasons": [str(e)],
                }
            except Exception as e:  # noqa: BLE001
                ctx.status = RunStatus.FAILED
                ctx.error = str(e)
                self.audit.emit(
                    run_id=ctx.run_id,
                    event_type="run.error",
                    actor=ctx.actor,
                    action=f"competency:{self.competency.id}:workflow",
                    error=str(e),
                )

        if ctx.status == RunStatus.RUNNING:
            ctx.status = RunStatus.SUCCEEDED

        ctx.finished_at = datetime.now(timezone.utc)
        self.audit.emit(
            run_id=ctx.run_id,
            event_type="run.end",
            actor=ctx.actor,
            action=f"competency:{self.competency.id}:execute",
            outputs={"status": ctx.status.value, "outputs": ctx.outputs},
            tokens_in=ctx.usage.prompt_tokens,
            tokens_out=ctx.usage.completion_tokens,
            cost_usd=ctx.usage.cost_usd,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

        # Update memory with the episode summary (only on success)
        if ctx.status == RunStatus.SUCCEEDED:
            self.memory.remember(
                competency_id=self.competency.id,
                type=MemoryType.EPISODIC,
                content=_episode_summary(ctx),
                metadata={"run_id": ctx.run_id, "status": ctx.status.value, "actor_id": ctx.actor.get("id")},
                importance=0.5,
            )

        return ctx, plan, self._evaluate(ctx)

    def _evaluate(self, ctx: RunContext) -> EvaluationResult:
        events = []
        first = self.audit.first_sink()
        if hasattr(first, "events"):
            events = [e for e in first.events if e.run_id == ctx.run_id]
        return self.evaluator.evaluate(ctx, events)

    def _retrieve_memory(self, *, goal: str | None, inputs: dict[str, Any]) -> list[str]:
        query = goal or " ".join(str(v) for v in inputs.values() if isinstance(v, (str, int, float)))
        entries = self.memory.recall(
            competency_id=self.competency.id,
            query=query or None,
            limit=8,
        )
        return [e.content for e in entries]


def _default_goal(ctx: RunContext) -> str:
    return f"Execute competency '{ctx.competency.name}' with inputs: {ctx.inputs}"


def _episode_summary(ctx: RunContext) -> str:
    return (
        f"Run {ctx.run_id} of '{ctx.competency.id}' completed with status={ctx.status.value}. "
        f"Inputs={list(ctx.inputs.keys())}; outputs={list(ctx.outputs.keys())}; "
        f"tokens={ctx.usage.total_tokens}; cost=${ctx.usage.cost_usd:.4f}."
    )
