"""Memory store — typed entries, filtered retrieval, retention.

In-memory implementation by default. Pluggable via the `MemoryBackend` protocol;
the API layer swaps in a SQLite-backed implementation.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from uce_core.models import MemoryType


@dataclass
class MemoryEntry:
    type: MemoryType
    competency_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5  # 0..1
    ttl_seconds: int | None = None  # None = forever

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.ttl_seconds is None:
            return False
        cutoff = (now or datetime.now(timezone.utc)) - timedelta(seconds=self.ttl_seconds)
        return self.created_at < cutoff


class MemoryBackend(Protocol):
    """Persistence backend for memory entries."""

    def add(self, entry: MemoryEntry) -> None: ...

    def list(
        self,
        *,
        competency_id: str | None = None,
        type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> list[MemoryEntry]: ...

    def delete(self, entry_id: str) -> bool: ...

    def all(self) -> list[MemoryEntry]: ...


class InMemoryBackend:
    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}

    def add(self, entry: MemoryEntry) -> None:
        self._entries[entry.id] = entry

    def list(
        self,
        *,
        competency_id: str | None = None,
        type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int | None = None,
    ) -> list[MemoryEntry]:
        out: list[MemoryEntry] = []
        for e in self._entries.values():
            if e.is_expired():
                continue
            if competency_id is not None and e.competency_id != competency_id:
                continue
            if type is not None and e.type != type:
                continue
            if tags and not set(tags).issubset(set(e.tags)):
                continue
            out.append(e)
        out.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        if limit is not None:
            out = out[:limit]
        return out

    def delete(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None

    def all(self) -> list[MemoryEntry]:
        return [e for e in self._entries.values() if not e.is_expired()]


class MemoryStore:
    """High-level memory API used by the runtime. Wraps a backend."""

    def __init__(self, backend: MemoryBackend | None = None) -> None:
        self.backend = backend or InMemoryBackend()

    def remember(
        self,
        *,
        competency_id: str,
        type: MemoryType,
        content: str,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        importance: float = 0.5,
        ttl_seconds: int | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            type=type,
            competency_id=competency_id,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
            importance=max(0.0, min(1.0, importance)),
            ttl_seconds=ttl_seconds,
        )
        self.backend.add(entry)
        return entry

    def recall(
        self,
        *,
        competency_id: str,
        types: list[MemoryType] | None = None,
        tags: list[str] | None = None,
        query: str | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Retrieve the most relevant entries.

        Without an embedding model wired in, we do tag/keyword scoring. The API
        layer can override this with semantic search.
        """
        candidates: list[MemoryEntry] = []
        for t in types or [None]:  # type: ignore[list-item]
            candidates.extend(
                self.backend.list(competency_id=competency_id, type=t, tags=tags, limit=None)
            )
        # De-dupe
        seen: set[str] = set()
        unique: list[MemoryEntry] = []
        for e in candidates:
            if e.id in seen:
                continue
            seen.add(e.id)
            unique.append(e)

        if query:
            q_lower = query.lower()
            tokens = [t for t in q_lower.split() if t]
            def score(entry: MemoryEntry) -> float:
                text = entry.content.lower()
                hits = sum(1 for t in tokens if t in text)
                return entry.importance + 0.1 * hits
            unique.sort(key=score, reverse=True)
        else:
            unique.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        return unique[:limit]

    def forget(self, entry_id: str) -> bool:
        return self.backend.delete(entry_id)

    def all(self, competency_id: str | None = None) -> list[MemoryEntry]:
        return [
            e
            for e in self.backend.all()
            if competency_id is None or e.competency_id == competency_id
        ]
