"""Audit logger — emits structured events for every run."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass
class AuditEvent:
    run_id: str
    span_id: str
    event_type: str  # e.g. "policy.check", "skill.start", "skill.end", "workflow.step", "error"
    actor: dict[str, Any]
    action: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    decision: str | None = None
    reasons: list[str] = field(default_factory=list)
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None: ...


class InMemorySink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


class JsonLinesSink:
    """Append events as JSON lines to a file."""

    def __init__(self, path: str) -> None:
        self.path = path

    def write(self, event: AuditEvent) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), default=str) + "\n")


# Patterns whose values should be redacted in audit logs.
_REDACT_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload  # type: ignore[unreachable]
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if any(p in k.lower() for p in _REDACT_KEYS):
            out[k] = "<redacted>"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out


class AuditLogger:
    """Emit audit events through one or more sinks, with automatic redaction."""

    def __init__(self, *sinks: AuditSink) -> None:
        self.sinks: list[AuditSink] = list(sinks) or [InMemorySink()]

    def emit(
        self,
        *,
        run_id: str,
        event_type: str,
        actor: dict[str, Any],
        action: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        decision: str | None = None,
        reasons: list[str] | None = None,
        latency_ms: int = 0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0,
        error: str | None = None,
        span_id: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            run_id=run_id,
            span_id=span_id or str(uuid.uuid4()),
            event_type=event_type,
            actor=_redact(actor),
            action=action,
            inputs=_redact(inputs or {}),
            outputs=_redact(outputs or {}),
            decision=decision,
            reasons=list(reasons or []),
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            error=error,
        )
        for sink in self.sinks:
            sink.write(event)
        return event

    def first_sink(self) -> AuditSink:
        return self.sinks[0]
