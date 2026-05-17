"""Evaluator — scores a finished run."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from uce_runtime.audit import AuditEvent
from uce_runtime.context import RunContext, RunStatus


@dataclass
class EvaluationResult:
    run_id: str
    competency_id: str
    success: bool
    status: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    policy_violations: int = 0
    escalations: int = 0
    step_count: int = 0
    error_count: int = 0
    confidence: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Evaluator:
    def __init__(self) -> None:
        pass

    def evaluate(self, ctx: RunContext, audit_events: list[AuditEvent]) -> EvaluationResult:
        policy_violations = sum(1 for e in audit_events if e.event_type == "policy.check" and e.decision == "deny")
        escalations = sum(1 for e in audit_events if e.event_type == "workflow.step.error" or e.decision == "require_approval")
        step_count = sum(1 for e in audit_events if e.event_type.startswith("workflow.step"))
        error_count = sum(1 for e in audit_events if e.error)
        latency = int(((ctx.finished_at or ctx.started_at) - ctx.started_at).total_seconds() * 1000)
        return EvaluationResult(
            run_id=ctx.run_id,
            competency_id=ctx.competency.id,
            success=ctx.status == RunStatus.SUCCEEDED,
            status=ctx.status.value,
            latency_ms=latency,
            tokens_in=ctx.usage.prompt_tokens,
            tokens_out=ctx.usage.completion_tokens,
            cost_usd=ctx.usage.cost_usd,
            policy_violations=policy_violations,
            escalations=escalations,
            step_count=step_count,
            error_count=error_count,
        )
