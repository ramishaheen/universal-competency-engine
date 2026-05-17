"""SQLAlchemy-backed MemoryBackend that satisfies the uce_runtime protocol."""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from uce_core.models import MemoryType
from uce_runtime.memory import MemoryEntry

from uce_api.db.models import MemoryRow


class SqlAlchemyMemoryBackend:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def _session(self) -> Session:
        return self._session_factory()

    def add(self, entry: MemoryEntry) -> None:
        with self._session() as db:
            row = MemoryRow(
                id=entry.id,
                competency_id=entry.competency_id,
                type=entry.type.value if isinstance(entry.type, MemoryType) else str(entry.type),
                content=entry.content,
                meta=entry.metadata,
                tags=entry.tags,
                importance=entry.importance,
                ttl_seconds=entry.ttl_seconds,
                created_at=entry.created_at,
            )
            db.add(row)
            db.commit()

    def list(
        self,
        *,
        competency_id: str | None = None,
        type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> list[MemoryEntry]:
        with self._session() as db:
            q = select(MemoryRow)
            if competency_id is not None:
                q = q.where(MemoryRow.competency_id == competency_id)
            if type is not None:
                q = q.where(MemoryRow.type == type.value)
            rows: Iterable[MemoryRow] = db.execute(q).scalars().all()
            entries = [_to_entry(r) for r in rows if not _expired(r)]
            if tags:
                entries = [e for e in entries if set(tags).issubset(set(e.tags))]
            entries.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
            return entries[:limit] if limit is not None else entries

    def delete(self, entry_id: str) -> bool:
        with self._session() as db:
            row = db.get(MemoryRow, entry_id)
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True

    def all(self) -> list[MemoryEntry]:
        return self.list()


def _to_entry(row: MemoryRow) -> MemoryEntry:
    return MemoryEntry(
        id=row.id,
        type=MemoryType(row.type),
        competency_id=row.competency_id,
        content=row.content,
        metadata=row.meta or {},
        tags=row.tags or [],
        importance=row.importance,
        ttl_seconds=row.ttl_seconds,
        created_at=row.created_at,
    )


def _expired(row: MemoryRow) -> bool:
    from datetime import datetime, timedelta, timezone

    if row.ttl_seconds is None:
        return False
    return row.created_at < datetime.now(timezone.utc) - timedelta(seconds=row.ttl_seconds)
