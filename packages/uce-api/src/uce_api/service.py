"""Service layer — shared execution logic used by the API and the CLI."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from uce_core import load_competency_from_dict
from uce_core.models import Competency
from uce_llm.base import LLMProvider
from uce_llm.registry import build_provider
from uce_runtime import AuditLogger, CompetencyExecutor, MemoryStore
from uce_runtime.audit import JsonLinesSink
from uce_runtime.context import RunContext, RunStatus

from uce_api.config import get_settings
from uce_api.db.memory_backend import SqlAlchemyMemoryBackend
from uce_api.db.models import AuditLogRow, CompetencyRow, EvaluationRow, ExecutionRow
from uce_api.db.session import SessionLocal


def build_llm_for_competency(competency: Competency) -> LLMProvider:
    settings = get_settings()
    provider = competency.llm.provider or settings.llm_provider
    model = competency.llm.model or settings.llm_model
    return build_provider(
        provider=provider,
        model=model,
        base_url=competency.llm.base_url,
        temperature=competency.llm.temperature,
        max_tokens=competency.llm.max_tokens,
    )


def execute_competency(
    *,
    db: Session,
    row: CompetencyRow,
    actor: dict[str, Any],
    inputs: dict[str, Any],
    goal: str | None,
    workflow_id: str | None,
    run_plan: bool,
) -> ExecutionRow:
    """Load the competency from the row, run it, persist execution + audit + evaluation."""
    competency = load_competency_from_dict(row.definition, source=f"db:{row.id}")
    llm = build_llm_for_competency(competency)
    memory = MemoryStore(backend=SqlAlchemyMemoryBackend(SessionLocal))
    settings = get_settings()
    sinks: list = []
    if settings.audit_log_file:
        os.makedirs(os.path.dirname(settings.audit_log_file) or ".", exist_ok=True)
        sinks.append(JsonLinesSink(settings.audit_log_file))
    audit = AuditLogger(*sinks) if sinks else AuditLogger()

    executor = CompetencyExecutor(
        competency=competency,
        llm=llm,
        memory=memory,
        audit=audit,
    )
    start = time.monotonic()
    import asyncio

    ctx, plan, evaluation = asyncio.run(
        executor.execute(
            inputs=inputs,
            actor=actor,
            workflow_id=workflow_id,
            goal=goal,
            run_plan=run_plan,
        )
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)

    exec_row = _persist_execution(db, ctx, plan, elapsed_ms)
    _persist_audit(db, ctx, audit, row.id)
    _persist_evaluation(db, ctx, evaluation)
    db.commit()
    db.refresh(exec_row)
    return exec_row


def _persist_execution(db: Session, ctx: RunContext, plan, elapsed_ms: int) -> ExecutionRow:
    row = ExecutionRow(
        id=ctx.run_id,
        competency_id=ctx.competency.id,
        actor_id=ctx.actor.get("id") if isinstance(ctx.actor.get("id"), str) else None,
        status=ctx.status.value,
        inputs=ctx.inputs,
        outputs=ctx.outputs,
        error=ctx.error,
        pending_approval=ctx.pending_approval,
        tokens_in=ctx.usage.prompt_tokens,
        tokens_out=ctx.usage.completion_tokens,
        cost_usd=ctx.usage.cost_usd,
        latency_ms=elapsed_ms,
        started_at=ctx.started_at,
        finished_at=ctx.finished_at,
        plan=_plan_to_dict(plan),
    )
    db.add(row)
    return row


def _plan_to_dict(plan) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        "goal": plan.goal,
        "rationale": plan.rationale,
        "steps": [
            {
                "description": s.description,
                "skill_id": s.skill_id,
                "rationale": s.rationale,
                "expected_output": s.expected_output,
            }
            for s in plan.steps
        ],
        "risk_score": plan.risk_score,
        "confidence": plan.confidence,
        "alignment_score": plan.alignment_score,
        "requires_human_approval": plan.requires_human_approval,
        "notes": plan.notes,
    }


def _persist_audit(db: Session, ctx: RunContext, audit: AuditLogger, competency_id: str) -> None:
    sink = audit.first_sink()
    if not hasattr(sink, "events"):
        return
    for ev in sink.events:
        if ev.run_id != ctx.run_id:
            continue
        db.add(
            AuditLogRow(
                run_id=ev.run_id,
                span_id=ev.span_id,
                competency_id=competency_id,
                event_type=ev.event_type,
                action=ev.action,
                actor=ev.actor,
                inputs=ev.inputs,
                outputs=ev.outputs,
                decision=ev.decision,
                reasons=ev.reasons,
                latency_ms=ev.latency_ms,
                tokens_in=ev.tokens_in,
                tokens_out=ev.tokens_out,
                cost_usd=ev.cost_usd,
                error=ev.error,
                created_at=ev.timestamp,
            )
        )


def _persist_evaluation(db: Session, ctx: RunContext, evaluation) -> None:
    db.add(
        EvaluationRow(
            run_id=evaluation.run_id,
            competency_id=evaluation.competency_id,
            success=evaluation.success,
            status=evaluation.status,
            latency_ms=evaluation.latency_ms,
            tokens_in=evaluation.tokens_in,
            tokens_out=evaluation.tokens_out,
            cost_usd=evaluation.cost_usd,
            policy_violations=evaluation.policy_violations,
            escalations=evaluation.escalations,
            step_count=evaluation.step_count,
            error_count=evaluation.error_count,
        )
    )
