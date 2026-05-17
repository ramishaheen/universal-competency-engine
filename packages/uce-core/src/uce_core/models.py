"""Pydantic schema for a Competency and all nested objects.

Reflects the 19-section spec:
- Competency Definition (mission, objectives, scope, metrics, risk, priority)
- Skills (atomic capabilities)
- Workflows (orchestration with sequential/parallel/conditional/approval steps)
- Policies (allow/deny/require_approval governance)
- Memory configuration (short/long/episodic/semantic/procedural/policy/decision/...)
- Agents (planner/researcher/analyst/executor/reviewer/governance/memory/reporting)
- Evaluation configuration
- LLM provider configuration
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepType(str, Enum):
    PROMPT = "prompt"  # LLM completion
    TOOL = "tool"  # External tool / API call
    PYTHON = "python"  # In-process python callable
    SKILL = "skill"  # Reference to another skill in this competency
    HTTP = "http"  # Arbitrary HTTP request


class WorkflowStepType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    APPROVAL = "approval"  # Human-in-the-loop
    SKILL = "skill"  # Invoke a skill
    SUB_WORKFLOW = "sub_workflow"
    ESCALATION = "escalation"


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    POLICY = "policy"
    DECISION = "decision"
    USER_PREFERENCE = "user_preference"
    ORGANIZATIONAL = "organizational"


class AgentRole(str, Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    GOVERNANCE = "governance"
    MEMORY = "memory"
    REPORTING = "reporting"


class TriggerType(str, Enum):
    MANUAL = "manual"
    EVENT = "event"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"


# ──────────────────────────────────────────────────────────────────────────────
# Common pieces
# ──────────────────────────────────────────────────────────────────────────────


class _Base(BaseModel):
    """Common config for all models — forbid unknown fields to catch typos early."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
    )


class Objective(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    priority: PriorityLevel = PriorityLevel.MEDIUM
    metric: str | None = None
    target_value: str | float | int | None = None


class ErrorHandling(_Base):
    retry_count: int = Field(default=0, ge=0, le=10)
    retry_backoff_seconds: float = Field(default=1.0, ge=0)
    fallback_skill: str | None = None
    on_error: Literal["raise", "skip", "fallback"] = "raise"


class PerformanceCriteria(_Base):
    max_latency_ms: int | None = Field(default=None, ge=0)
    max_tokens: int | None = Field(default=None, ge=0)
    max_cost_usd: float | None = Field(default=None, ge=0)
    min_confidence: float | None = Field(default=None, ge=0, le=1)


# ──────────────────────────────────────────────────────────────────────────────
# Skill
# ──────────────────────────────────────────────────────────────────────────────


class SkillStep(_Base):
    """One executable step inside a skill."""

    id: str = Field(min_length=1)
    type: StepType
    description: str = ""
    # ── Step bodies (only one of these is meaningful per type) ──
    prompt: str | None = None  # for type=prompt
    tool: str | None = None  # for type=tool
    python_callable: str | None = None  # for type=python (module:func)
    skill: str | None = None  # for type=skill (id of another skill)
    http: dict[str, Any] | None = None  # for type=http
    # ── Common ──
    inputs: dict[str, Any] = Field(default_factory=dict)
    output_key: str | None = None  # where to put the result in run context
    when: str | None = None  # python-like condition string evaluated against ctx
    error_handling: ErrorHandling = Field(default_factory=ErrorHandling)

    @model_validator(mode="after")
    def _check_body(self) -> "SkillStep":
        bodies = {
            StepType.PROMPT: self.prompt,
            StepType.TOOL: self.tool,
            StepType.PYTHON: self.python_callable,
            StepType.SKILL: self.skill,
            StepType.HTTP: self.http,
        }
        required = bodies[self.type]
        if required is None:
            raise ValueError(f"step '{self.id}' of type {self.type.value} requires the matching body field")
        return self


class Skill(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    output_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    required_tools: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    execution_steps: list[SkillStep] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # ids of other skills
    error_handling: ErrorHandling = Field(default_factory=ErrorHandling)
    performance_criteria: PerformanceCriteria = Field(default_factory=PerformanceCriteria)
    tags: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Workflow
# ──────────────────────────────────────────────────────────────────────────────


class WorkflowStep(_Base):
    id: str = Field(min_length=1)
    type: WorkflowStepType
    description: str = ""

    # for type=skill
    skill: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    output_key: str | None = None

    # for type=conditional
    when: str | None = None  # condition expression evaluated against run context
    then: list["WorkflowStep"] = Field(default_factory=list)
    otherwise: list["WorkflowStep"] = Field(default_factory=list)

    # for type=parallel | sequential
    children: list["WorkflowStep"] = Field(default_factory=list)

    # for type=approval
    approval_role: str | None = None
    approval_message: str | None = None

    # for type=sub_workflow
    sub_workflow: str | None = None

    # for type=escalation
    escalation_role: str | None = None
    escalation_reason: str | None = None

    # common
    on_error: Literal["raise", "skip", "fallback", "escalate"] = "raise"
    fallback_step: str | None = None
    retry_count: int = Field(default=0, ge=0, le=10)

    @model_validator(mode="after")
    def _check_body(self) -> "WorkflowStep":
        match self.type:
            case WorkflowStepType.SKILL if not self.skill:
                raise ValueError(f"workflow step '{self.id}' (skill) requires `skill`")
            case WorkflowStepType.CONDITIONAL if not self.when:
                raise ValueError(f"workflow step '{self.id}' (conditional) requires `when`")
            case WorkflowStepType.APPROVAL if not self.approval_role:
                raise ValueError(f"workflow step '{self.id}' (approval) requires `approval_role`")
            case WorkflowStepType.SUB_WORKFLOW if not self.sub_workflow:
                raise ValueError(f"workflow step '{self.id}' (sub_workflow) requires `sub_workflow`")
            case WorkflowStepType.ESCALATION if not self.escalation_role:
                raise ValueError(f"workflow step '{self.id}' (escalation) requires `escalation_role`")
            case WorkflowStepType.PARALLEL | WorkflowStepType.SEQUENTIAL:
                if not self.children:
                    raise ValueError(f"workflow step '{self.id}' ({self.type.value}) requires `children`")
        return self


WorkflowStep.model_rebuild()


class Workflow(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    trigger: TriggerType = TriggerType.MANUAL
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    steps: list[WorkflowStep]
    completion_criteria: str | None = None  # expression on ctx
    is_default: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Policy
# ──────────────────────────────────────────────────────────────────────────────


class Policy(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    effect: PolicyEffect
    # `applies_to` is a list of action-pattern strings (e.g. "skill:contract_review",
    # "*:execute", "workflow:procurement_main"). Matched by simple glob.
    applies_to: list[str] = Field(default_factory=lambda: ["*"])
    # `when` is an optional condition expression on the run context.
    when: str | None = None
    required_role: str | None = None  # for require_approval / role-gated allow
    compliance_tags: list[str] = Field(default_factory=list)
    sensitivity: Literal["public", "internal", "confidential", "restricted"] = "internal"
    audit_required: bool = True
    reason: str = ""

    @field_validator("applies_to")
    @classmethod
    def _nonempty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("`applies_to` must contain at least one pattern")
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Memory & Evaluation config
# ──────────────────────────────────────────────────────────────────────────────


class MemoryTypeConfig(_Base):
    type: MemoryType
    enabled: bool = True
    retention_days: int | None = Field(default=None, ge=0)  # None = forever
    max_entries: int | None = Field(default=None, ge=0)
    retrieval_top_k: int = Field(default=5, ge=0, le=100)


class MemoryConfig(_Base):
    types: list[MemoryTypeConfig] = Field(
        default_factory=lambda: [
            MemoryTypeConfig(type=MemoryType.SHORT_TERM, retention_days=1),
            MemoryTypeConfig(type=MemoryType.LONG_TERM),
            MemoryTypeConfig(type=MemoryType.EPISODIC, retention_days=365),
            MemoryTypeConfig(type=MemoryType.SEMANTIC),
            MemoryTypeConfig(type=MemoryType.PROCEDURAL),
            MemoryTypeConfig(type=MemoryType.POLICY),
            MemoryTypeConfig(type=MemoryType.DECISION, retention_days=730),
            MemoryTypeConfig(type=MemoryType.USER_PREFERENCE),
            MemoryTypeConfig(type=MemoryType.ORGANIZATIONAL),
        ]
    )
    embedding_model: str = "text-embedding-3-small"
    knowledge_sources: list[str] = Field(default_factory=list)


class EvaluationConfig(_Base):
    track_accuracy: bool = True
    track_latency: bool = True
    track_tokens: bool = True
    track_cost: bool = True
    track_policy_violations: bool = True
    track_escalations: bool = True
    track_user_satisfaction: bool = False
    success_threshold: float = Field(default=0.8, ge=0, le=1)
    failure_threshold: float = Field(default=0.5, ge=0, le=1)


# ──────────────────────────────────────────────────────────────────────────────
# Agents
# ──────────────────────────────────────────────────────────────────────────────


class Agent(_Base):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    role: AgentRole
    description: str = ""
    system_prompt: str = ""
    tools: list[str] = Field(default_factory=list)
    model_override: str | None = None  # if set, this agent uses a different LLM


# ──────────────────────────────────────────────────────────────────────────────
# LLM config
# ──────────────────────────────────────────────────────────────────────────────


class LLMConfig(_Base):
    provider: Literal["anthropic", "openai", "ollama"] = "anthropic"
    model: str = "claude-sonnet-4-6"
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1)
    base_url: str | None = None  # for local ollama / custom endpoints
    extra: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Competency (top-level)
# ──────────────────────────────────────────────────────────────────────────────


class Competency(_Base):
    """Top-level Competency definition.

    Maps to your spec's section 1 "Competency Definition Layer" with all
    surrounding layers attached.
    """

    # Section 1 — Definition
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_\-]+$")
    name: str
    version: str = "0.1.0"
    description: str = ""
    domain: str = ""
    mission: str = ""
    objectives: list[Objective] = Field(default_factory=list)
    expected_outcomes: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    scope: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    priority_level: PriorityLevel = PriorityLevel.MEDIUM
    required_inputs: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    expected_outputs: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})

    # Section 2-8 — Layers
    skills: list[Skill] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    policies: list[Policy] = Field(default_factory=list)
    agents: list[Agent] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Free-form metadata for org-specific fields
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    # Convenience accessors
    def skill_by_id(self, sid: str) -> Skill | None:
        return next((s for s in self.skills if s.id == sid), None)

    def workflow_by_id(self, wid: str) -> Workflow | None:
        return next((w for w in self.workflows if w.id == wid), None)

    def default_workflow(self) -> Workflow | None:
        if not self.workflows:
            return None
        defaults = [w for w in self.workflows if w.is_default]
        return defaults[0] if defaults else self.workflows[0]
