"""Workflow engine — executes a Workflow tree against a RunContext.

Supports sequential, parallel, conditional, approval, skill, sub_workflow, escalation.
Emits audit events for every step. Honors policy decisions and approval suspension.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from uce_core.models import Workflow, WorkflowStep, WorkflowStepType

from uce_runtime.audit import AuditLogger
from uce_runtime.context import RunContext, RunStatus
from uce_runtime.errors import ExecutionError, PolicyDenied, PolicyRequiresApproval
from uce_runtime.expressions import EvalError, safe_eval
from uce_runtime.policy import PolicyEngine
from uce_runtime.skills import SkillExecutor


class WorkflowEngine:
    def __init__(
        self,
        *,
        skill_executor: SkillExecutor,
        policy: PolicyEngine,
        audit: AuditLogger,
    ) -> None:
        self.skills = skill_executor
        self.policy = policy
        self.audit = audit

    async def run(self, workflow: Workflow, ctx: RunContext) -> dict[str, Any]:
        await self._execute_steps(workflow.steps, ctx, wf_id=workflow.id)
        ctx.outputs = ctx.data.copy()
        return ctx.outputs

    async def _execute_steps(self, steps: list[WorkflowStep], ctx: RunContext, *, wf_id: str) -> None:
        for step in steps:
            await self._execute_step(step, ctx, wf_id=wf_id)
            if ctx.status == RunStatus.PENDING_APPROVAL:
                return

    async def _execute_step(self, step: WorkflowStep, ctx: RunContext, *, wf_id: str) -> Any:
        start = time.monotonic()
        # Policy check
        action = f"workflow:{wf_id}:step:{step.id}"
        decision = self.policy.check(action, ctx.eval_context())
        self.audit.emit(
            run_id=ctx.run_id,
            event_type="policy.check",
            actor=ctx.actor,
            action=action,
            decision=decision.effect.value,
            reasons=decision.reasons,
        )
        if decision.denied:
            raise PolicyDenied(action=action, reason="; ".join(decision.reasons), policy_id=",".join(decision.matched))
        if decision.needs_approval:
            ctx.status = RunStatus.PENDING_APPROVAL
            ctx.pending_approval = {
                "step_id": step.id,
                "workflow_id": wf_id,
                "required_role": decision.required_role,
                "reasons": decision.reasons,
            }
            return None

        # Dispatch by step type
        try:
            result = await self._dispatch(step, ctx, wf_id=wf_id)
            self.audit.emit(
                run_id=ctx.run_id,
                event_type="workflow.step.success",
                actor=ctx.actor,
                action=action,
                outputs={"result_preview": _preview(result)},
                latency_ms=int((time.monotonic() - start) * 1000),
            )
            if step.output_key and result is not None:
                ctx.data[step.output_key] = result
            return result
        except (PolicyDenied, PolicyRequiresApproval):
            raise
        except Exception as e:  # noqa: BLE001
            self.audit.emit(
                run_id=ctx.run_id,
                event_type="workflow.step.error",
                actor=ctx.actor,
                action=action,
                error=str(e),
                latency_ms=int((time.monotonic() - start) * 1000),
            )
            if step.on_error == "skip":
                return None
            if step.on_error == "escalate":
                ctx.status = RunStatus.PENDING_APPROVAL
                ctx.pending_approval = {
                    "step_id": step.id,
                    "workflow_id": wf_id,
                    "required_role": "admin",
                    "reasons": [f"escalated due to error: {e}"],
                }
                return None
            raise ExecutionError(step.id, str(e), cause=e) from e

    async def _dispatch(self, step: WorkflowStep, ctx: RunContext, *, wf_id: str) -> Any:
        match step.type:
            case WorkflowStepType.SKILL:
                skill = ctx.competency.skill_by_id(step.skill or "")
                if skill is None:
                    raise ExecutionError(step.id, f"unknown skill '{step.skill}'")
                rendered = _render_inputs(step.inputs, ctx)
                return await self.skills.run(skill, ctx, inputs=rendered)

            case WorkflowStepType.SEQUENTIAL:
                await self._execute_steps(step.children, ctx, wf_id=wf_id)
                return None

            case WorkflowStepType.PARALLEL:
                await asyncio.gather(
                    *(self._execute_step(child, ctx, wf_id=wf_id) for child in step.children)
                )
                return None

            case WorkflowStepType.CONDITIONAL:
                truthy = False
                try:
                    truthy = bool(safe_eval(step.when or "False", ctx.eval_context()))
                except EvalError as e:
                    raise ExecutionError(step.id, f"`when` failed: {e}", cause=e) from e
                branch = step.then if truthy else step.otherwise
                await self._execute_steps(branch, ctx, wf_id=wf_id)
                return None

            case WorkflowStepType.APPROVAL:
                ctx.status = RunStatus.PENDING_APPROVAL
                ctx.pending_approval = {
                    "step_id": step.id,
                    "workflow_id": wf_id,
                    "required_role": step.approval_role,
                    "reasons": [step.approval_message or "approval required"],
                }
                return None

            case WorkflowStepType.SUB_WORKFLOW:
                sub = ctx.competency.workflow_by_id(step.sub_workflow or "")
                if sub is None:
                    raise ExecutionError(step.id, f"unknown sub-workflow '{step.sub_workflow}'")
                await self.run(sub, ctx)
                return None

            case WorkflowStepType.ESCALATION:
                ctx.status = RunStatus.PENDING_APPROVAL
                ctx.pending_approval = {
                    "step_id": step.id,
                    "workflow_id": wf_id,
                    "required_role": step.escalation_role,
                    "reasons": [step.escalation_reason or "escalation"],
                }
                return None

        raise ExecutionError(step.id, f"unhandled workflow step type: {step.type}")


def _render_inputs(inputs: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Workflow-level input rendering — supports {{var}} substitution from eval context."""
    from jinja2 import Environment, StrictUndefined

    env = Environment(undefined=StrictUndefined, autoescape=False)
    out: dict[str, Any] = {}
    for k, v in (inputs or {}).items():
        if isinstance(v, str):
            try:
                out[k] = env.from_string(v).render(**ctx.eval_context())
            except Exception:  # noqa: BLE001 — pass-through on render error
                out[k] = v
        else:
            out[k] = v
    return out


def _preview(value: Any, limit: int = 200) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…"
    if isinstance(value, (dict, list)):
        s = str(value)
        return s if len(s) <= limit else s[:limit] + "…"
    return value
