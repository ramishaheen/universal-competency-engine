from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from uce_api.auth import require_permissions
from uce_api.db.models import AuditLogRow, User
from uce_api.db.session import get_session
from uce_api.schemas import AuditOut

router = APIRouter(tags=["audit"])


@router.get("/audit", response_model=list[AuditOut])
def list_audit(
    competency_id: str | None = None,
    run_id: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=200, le=2000),
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("audit.read")),
) -> list[AuditOut]:
    q = db.query(AuditLogRow)
    if competency_id:
        q = q.filter(AuditLogRow.competency_id == competency_id)
    if run_id:
        q = q.filter(AuditLogRow.run_id == run_id)
    if event_type:
        q = q.filter(AuditLogRow.event_type == event_type)
    rows = q.order_by(AuditLogRow.created_at.desc()).limit(limit).all()
    return [
        AuditOut(
            id=r.id,
            run_id=r.run_id,
            competency_id=r.competency_id,
            event_type=r.event_type,
            action=r.action,
            actor=r.actor or {},
            inputs=r.inputs or {},
            outputs=r.outputs or {},
            decision=r.decision,
            reasons=r.reasons or [],
            latency_ms=r.latency_ms,
            tokens_in=r.tokens_in,
            tokens_out=r.tokens_out,
            cost_usd=r.cost_usd,
            error=r.error,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/competencies/{competency_id}/audit-log", response_model=list[AuditOut])
def audit_for_competency(
    competency_id: str,
    limit: int = Query(default=200, le=2000),
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("audit.read")),
) -> list[AuditOut]:
    return list_audit(competency_id=competency_id, limit=limit, db=db, _=_)
