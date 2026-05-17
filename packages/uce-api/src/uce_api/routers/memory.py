from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from uce_api.auth import require_permissions
from uce_api.db.models import CompetencyRow, MemoryRow, User
from uce_api.db.session import get_session
from uce_api.schemas import MemoryIn, MemoryOut, StatusOut

router = APIRouter(prefix="/competencies/{competency_id}/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
def list_memory(
    competency_id: str,
    type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("memory.read")),
) -> list[MemoryOut]:
    if db.get(CompetencyRow, competency_id) is None:
        raise HTTPException(status_code=404, detail="competency not found")
    q = db.query(MemoryRow).filter(MemoryRow.competency_id == competency_id)
    if type:
        q = q.filter(MemoryRow.type == type)
    rows = q.order_by(MemoryRow.created_at.desc()).limit(limit).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=MemoryOut, status_code=201)
def add_memory(
    competency_id: str,
    body: MemoryIn,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("memory.write")),
) -> MemoryOut:
    if db.get(CompetencyRow, competency_id) is None:
        raise HTTPException(status_code=404, detail="competency not found")
    row = MemoryRow(
        competency_id=competency_id,
        type=body.type,
        content=body.content,
        meta=body.metadata,
        tags=body.tags,
        importance=body.importance,
        ttl_seconds=body.ttl_seconds,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{entry_id}", response_model=StatusOut)
def delete_memory(
    competency_id: str,
    entry_id: str,
    db: Session = Depends(get_session),
    _: User = Depends(require_permissions("memory.write")),
) -> StatusOut:
    row = db.get(MemoryRow, entry_id)
    if row is None or row.competency_id != competency_id:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(row)
    db.commit()
    return StatusOut(status="deleted")


def _to_out(row: MemoryRow) -> MemoryOut:
    return MemoryOut(
        id=row.id,
        competency_id=row.competency_id,
        type=row.type,
        content=row.content,
        metadata=row.meta or {},
        tags=row.tags or [],
        importance=row.importance,
        ttl_seconds=row.ttl_seconds,
        created_at=row.created_at,
    )
