"""Request/response Pydantic schemas for the API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Auth ─────────────────────────────────────────────────────────────────────


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(_M):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[str] = []


# ── Competency ───────────────────────────────────────────────────────────────


class CompetencyCreate(BaseModel):
    """Accepts a full Competency definition (validated upstream by uce_core)."""

    definition: dict[str, Any]


class CompetencyUpdate(BaseModel):
    definition: dict[str, Any]


class CompetencyOut(_M):
    id: str
    name: str
    version: str
    description: str
    domain: str
    risk_level: str
    priority_level: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompetencyDetail(CompetencyOut):
    definition: dict[str, Any]


# ── Execution ────────────────────────────────────────────────────────────────


class ExecuteIn(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    goal: str | None = None
    workflow_id: str | None = None
    run_plan: bool = True


class ExecutionOut(_M):
    id: str
    competency_id: str
    status: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error: str | None
    pending_approval: dict[str, Any] | None
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int
    started_at: datetime
    finished_at: datetime | None
    plan: dict[str, Any] | None


class ApproveIn(BaseModel):
    approved: bool = True
    note: str = ""


# ── Memory ───────────────────────────────────────────────────────────────────


class MemoryIn(BaseModel):
    type: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    importance: float = 0.5
    ttl_seconds: int | None = None


class MemoryOut(_M):
    id: str
    competency_id: str
    type: str
    content: str
    meta: dict[str, Any] = Field(alias="metadata")
    tags: list[str]
    importance: float
    ttl_seconds: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Audit / Performance ──────────────────────────────────────────────────────


class AuditOut(_M):
    id: str
    run_id: str
    competency_id: str | None
    event_type: str
    action: str
    actor: dict[str, Any]
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    decision: str | None
    reasons: list[str]
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    error: str | None
    created_at: datetime


class PerformanceOut(BaseModel):
    competency_id: str
    runs: int
    success_rate: float
    avg_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    avg_policy_violations: float
    avg_escalations: float


# ── Generic ──────────────────────────────────────────────────────────────────


class StatusOut(BaseModel):
    status: str
    detail: str = ""
