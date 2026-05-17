from __future__ import annotations

from uce_runtime.audit import AuditLogger, InMemorySink


def test_emit_and_collect():
    sink = InMemorySink()
    log = AuditLogger(sink)
    e = log.emit(
        run_id="r1",
        event_type="policy.check",
        actor={"id": "u1", "roles": ["operator"]},
        action="skill:x",
        decision="allow",
        reasons=["ok"],
    )
    assert e.run_id == "r1"
    assert sink.events == [e]


def test_redacts_secrets():
    sink = InMemorySink()
    log = AuditLogger(sink)
    log.emit(
        run_id="r2",
        event_type="skill.start",
        actor={"id": "u1", "api_key": "real-secret"},
        action="skill:y",
        inputs={"password": "hunter2", "user": "x"},
    )
    e = sink.events[0]
    assert e.actor["api_key"] == "<redacted>"
    assert e.inputs["password"] == "<redacted>"
    assert e.inputs["user"] == "x"
