from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from uce_api.auth import require_permissions
from uce_api.db.models import CompetencyRow, ExecutionRow, User
from uce_api.db.session import get_session
from uce_api.routers.competencies import _to_execution_out
from uce_api.schemas import ApproveIn, ExecuteIn, ExecutionOut, StatusOut
from uce_api.service import execute_competency
from uce_api.auth import actor_dict

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionOut])
def list_executions(
    competency_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.read")),
) -> list[ExecutionOut]:
    q = db.query(ExecutionRow)
    if competency_id:
        q = q.filter(ExecutionRow.competency_id == competency_id)
    if status:
        q = q.filter(ExecutionRow.status == status)
    rows = q.order_by(ExecutionRow.started_at.desc()).limit(limit).all()
    return [_to_execution_out(r) for r in rows]


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("competency.read")),
) -> ExecutionOut:
    row = db.get(ExecutionRow, execution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_execution_out(row)


@router.post("/{execution_id}/approve", response_model=ExecutionOut)
def approve_execution(
    execution_id: str,
    body: ApproveIn,
    db: Session = Depends(get_session),
    user: User = Depends(require_permissions("competency.approve")),
) -> ExecutionOut:
    row = db.get(ExecutionRow, execution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    if row.status != "pending_approval":
        raise HTTPException(status_code=400, detail=f"execution is not pending approval (status={row.status})")

    if not body.approved:
        row.status = "denied"
        row.error = f"denied by {user.email}: {body.note}"
        row.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _to_execution_out(row)

    # Approved: re-run the workflow with elevated role context.
    comp_row = db.get(CompetencyRow, row.competency_id)
    if comp_row is None:
        raise HTTPException(status_code=410, detail="competency no longer exists")

    actor = actor_dict(user)
    # Tag the actor with the required role for this resumed run so policies accept it.
    required_role = (row.pending_approval or {}).get("required_role")
    if required_role and required_role not in actor["roles"]:
        actor["roles"] = list(actor["roles"]) + [required_role]

    new_row = execute_competency(
        db=db,
        row=comp_row,
        actor=actor,
        inputs=row.inputs,
        goal=None,
        workflow_id=None,
        run_plan=False,
    )
    # Mark the original as resumed.
    row.status = "resumed"
    row.outputs = {"resumed_as": new_row.id}
    row.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(new_row)
    return _to_execution_out(new_row)
