from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from uce_core import load_competency_from_dict
from uce_core.errors import LoaderError
from uce_core.validator import validate_competency

from uce_api.auth import actor_dict, get_current_user, require_permissions
from uce_api.db.models import CompetencyRow, ExecutionRow, User
from uce_api.db.session import get_session
from uce_api.schemas import (
    CompetencyCreate,
    CompetencyDetail,
    CompetencyOut,
    CompetencyUpdate,
    ExecuteIn,
    ExecutionOut,
    StatusOut,
)
from uce_api.service import execute_competency

router = APIRouter(prefix="/competencies", tags=["competencies"])


def _to_detail(row: CompetencyRow) -> CompetencyDetail:
    return CompetencyDetail(
        id=row.id,
        name=row.name,
        version=row.version,
        description=row.description,
        domain=row.domain,
        risk_level=row.risk_level,
        priority_level=row.priority_level,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        definition=row.definition,
    )


def _validate(definition: dict[str, Any]) -> Any:
    try:
        c = load_competency_from_dict(definition)
    except LoaderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    issues = validate_competency(c)
    if issues:
        raise HTTPException(status_code=400, detail={"validation_issues": issues})
    return c


@router.post("", response_model=CompetencyDetail, status_code=201)
def create(
    body: CompetencyCreate,
    db: Session = Depends(get_session),
    user: User = Depends(require_permissions("competency.write")),
) -> CompetencyDetail:
    c = _validate(body.definition)
    if db.get(CompetencyRow, c.id):
        raise HTTPException(status_code=400, detail=f"competency '{c.id}' already exists")
    row = CompetencyRow(
        id=c.id,
        version=c.version,
        name=c.name,
        description=c.description,
        domain=c.domain,
        risk_level=c.risk_level.value,
        priority_level=c.priority_level.value,
        definition=body.definition,
        owner_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_detail(row)


@router.get("", response_model=list[CompetencyOut])
def list_all(
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.read")),
) -> list[CompetencyOut]:
    rows = db.query(CompetencyRow).order_by(CompetencyRow.created_at.desc()).all()
    return [
        CompetencyOut(
            id=r.id,
            name=r.name,
            version=r.version,
            description=r.description,
            domain=r.domain,
            risk_level=r.risk_level,
            priority_level=r.priority_level,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/{competency_id}", response_model=CompetencyDetail)
def get(
    competency_id: str,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.read")),
) -> CompetencyDetail:
    row = db.get(CompetencyRow, competency_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_detail(row)


@router.put("/{competency_id}", response_model=CompetencyDetail)
def update(
    competency_id: str,
    body: CompetencyUpdate,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.write")),
) -> CompetencyDetail:
    row = db.get(CompetencyRow, competency_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    c = _validate(body.definition)
    if c.id != competency_id:
        raise HTTPException(status_code=400, detail="definition.id must match URL id")
    row.name = c.name
    row.version = c.version
    row.description = c.description
    row.domain = c.domain
    row.risk_level = c.risk_level.value
    row.priority_level = c.priority_level.value
    row.definition = body.definition
    db.commit()
    db.refresh(row)
    return _to_detail(row)


@router.delete("/{competency_id}", response_model=StatusOut)
def delete(
    competency_id: str,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.write")),
) -> StatusOut:
    row = db.get(CompetencyRow, competency_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(row)
    db.commit()
    return StatusOut(status="deleted")


@router.post("/{competency_id}/execute", response_model=ExecutionOut, status_code=201)
def execute(
    competency_id: str,
    body: ExecuteIn,
    db: Session = Depends(get_session),
    user: User = Depends(require_permissions("competency.execute")),
) -> ExecutionOut:
    row = db.get(CompetencyRow, competency_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    exec_row = execute_competency(
        db=db,
        row=row,
        actor=actor_dict(user),
        inputs=body.inputs,
        goal=body.goal,
        workflow_id=body.workflow_id,
        run_plan=body.run_plan,
    )
    return _to_execution_out(exec_row)


@router.post("/validate", response_model=StatusOut)
def validate_only(
    body: CompetencyCreate,
    _: User = Depends(get_current_user),
) -> StatusOut:
    _validate(body.definition)
    return StatusOut(status="ok", detail="definition is valid")


def _to_execution_out(row: ExecutionRow) -> ExecutionOut:
    return ExecutionOut(
        id=row.id,
        competency_id=row.competency_id,
        status=row.status,
        inputs=row.inputs,
        outputs=row.outputs,
        error=row.error,
        pending_approval=row.pending_approval,
        tokens_in=row.tokens_in,
        tokens_out=row.tokens_out,
        cost_usd=row.cost_usd,
        latency_ms=row.latency_ms,
        started_at=row.started_at,
        finished_at=row.finished_at,
        plan=row.plan,
    )
