from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from uce_api.auth import require_permissions
from uce_api.db.models import CompetencyRow, EvaluationRow, User
from uce_api.db.session import get_session
from uce_api.schemas import PerformanceOut

router = APIRouter(tags=["performance"])


@router.get("/competencies/{competency_id}/performance", response_model=PerformanceOut)
def performance(
    competency_id: str,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("audit.read")),
) -> PerformanceOut:
    if db.get(CompetencyRow, competency_id) is None:
        raise HTTPException(status_code=404, detail="competency not found")

    base = db.query(EvaluationRow).filter(EvaluationRow.competency_id == competency_id)
    runs = base.count()
    if runs == 0:
        return PerformanceOut(
            competency_id=competency_id,
            runs=0,
            success_rate=0.0,
            avg_latency_ms=0.0,
            total_tokens=0,
            total_cost_usd=0.0,
            avg_policy_violations=0.0,
            avg_escalations=0.0,
        )
    succ = base.filter(EvaluationRow.success.is_(True)).count()
    avg_lat = base.with_entities(func.avg(EvaluationRow.latency_ms)).scalar() or 0
    tin = base.with_entities(func.sum(EvaluationRow.tokens_in)).scalar() or 0
    tout = base.with_entities(func.sum(EvaluationRow.tokens_out)).scalar() or 0
    cost = base.with_entities(func.sum(EvaluationRow.cost_usd)).scalar() or 0.0
    avg_pv = base.with_entities(func.avg(EvaluationRow.policy_violations)).scalar() or 0
    avg_esc = base.with_entities(func.avg(EvaluationRow.escalations)).scalar() or 0
    return PerformanceOut(
        competency_id=competency_id,
        runs=runs,
        success_rate=round(succ / runs, 4),
        avg_latency_ms=float(avg_lat),
        total_tokens=int(tin) + int(tout),
        total_cost_usd=float(cost),
        avg_policy_violations=float(avg_pv),
        avg_escalations=float(avg_esc),
    )
