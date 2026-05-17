"""Run context — shared state shuttled through every step of an execution."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from uce_core.models import Competency
from uce_llm.base import TokenUsage


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


@dataclass
class RunContext:
    """Mutable state for a single competency execution.

    Steps read from / write to `data`. `actor` carries identity for policy checks.
    """

    competency: Competency
    inputs: dict[str, Any]
    actor: dict[str, Any] = field(default_factory=lambda: {"id": "anonymous", "roles": ["operator"]})
    data: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    status: RunStatus = RunStatus.PENDING
    usage: TokenUsage = field(default_factory=TokenUsage)
    error: str | None = None
    pending_approval: dict[str, Any] | None = None  # populated when status=pending_approval

    # Per-skill output cache (skill_id -> last output)
    skill_results: dict[str, Any] = field(default_factory=dict)

    def add_usage(self, u: TokenUsage) -> None:
        self.usage = TokenUsage(
            prompt_tokens=self.usage.prompt_tokens + u.prompt_tokens,
            completion_tokens=self.usage.completion_tokens + u.completion_tokens,
            total_tokens=self.usage.total_tokens + u.total_tokens,
            cost_usd=round(self.usage.cost_usd + u.cost_usd, 6),
        )

    def eval_context(self) -> dict[str, Any]:
        """Snapshot dict used by safe_eval inside step conditions."""
        return {
            "inputs": self.inputs,
            "data": self.data,
            "outputs": self.outputs,
            "actor": self.actor,
            "skill_results": self.skill_results,
            "competency": {
                "id": self.competency.id,
                "name": self.competency.name,
                "domain": self.competency.domain,
            },
        }
