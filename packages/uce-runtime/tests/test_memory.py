from __future__ import annotations

import time

from uce_core.models import MemoryType
from uce_runtime.memory import MemoryEntry, MemoryStore


def test_remember_and_recall():
    s = MemoryStore()
    s.remember(competency_id="c1", type=MemoryType.SEMANTIC, content="vendors must be GDPR compliant", importance=0.9)
    s.remember(competency_id="c1", type=MemoryType.SEMANTIC, content="prefer local suppliers", importance=0.5)
    out = s.recall(competency_id="c1", query="GDPR")
    assert out[0].content.startswith("vendors must be GDPR")


def test_filter_by_type():
    s = MemoryStore()
    s.remember(competency_id="c1", type=MemoryType.EPISODIC, content="ran on Tuesday")
    s.remember(competency_id="c1", type=MemoryType.SEMANTIC, content="rule X")
    out = s.recall(competency_id="c1", types=[MemoryType.EPISODIC])
    assert len(out) == 1
    assert out[0].type == MemoryType.EPISODIC


def test_competency_isolation():
    s = MemoryStore()
    s.remember(competency_id="c1", type=MemoryType.SEMANTIC, content="x")
    s.remember(competency_id="c2", type=MemoryType.SEMANTIC, content="y")
    assert len(s.all("c1")) == 1
    assert len(s.all("c2")) == 1


def test_forget():
    s = MemoryStore()
    e = s.remember(competency_id="c1", type=MemoryType.LONG_TERM, content="x")
    assert s.forget(e.id) is True
    assert s.forget(e.id) is False


def test_ttl_expiry():
    e = MemoryEntry(type=MemoryType.SHORT_TERM, competency_id="c1", content="x", ttl_seconds=0)
    time.sleep(0.01)
    assert e.is_expired() is True
