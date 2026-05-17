"""Schema unit tests for uce-core models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from uce_core import (
    Competency,
    LLMConfig,
    Objective,
    Policy,
    PolicyEffect,
    PriorityLevel,
    RiskLevel,
    Skill,
    SkillStep,
    StepType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
)


def test_minimal_competency_validates():
    c = Competency(id="minimal", name="Minimal Competency")
    assert c.id == "minimal"
    assert c.risk_level == RiskLevel.MEDIUM
    assert c.priority_level == PriorityLevel.MEDIUM
    assert c.llm.provider == "anthropic"


def test_full_competency_round_trip():
    skill = Skill(
        id="echo",
        name="Echo",
        execution_steps=[
            SkillStep(id="s1", type=StepType.PROMPT, prompt="echo {{input}}"),
        ],
    )
    wf = Workflow(
        id="main",
        name="Main",
        is_default=True,
        steps=[
            WorkflowStep(id="run_echo", type=WorkflowStepType.SKILL, skill="echo"),
        ],
    )
    policy = Policy(
        id="allow_all",
        name="Allow All",
        effect=PolicyEffect.ALLOW,
        applies_to=["*"],
    )
    c = Competency(
        id="demo",
        name="Demo",
        mission="Echo things",
        objectives=[Objective(id="be_loud", name="Echo loudly")],
        skills=[skill],
        workflows=[wf],
        policies=[policy],
        llm=LLMConfig(provider="anthropic", model="claude-sonnet-4-6"),
    )
    assert c.skill_by_id("echo") is skill
    assert c.workflow_by_id("main") is wf
    assert c.default_workflow() is wf


def test_skill_step_requires_matching_body():
    with pytest.raises(PydanticValidationError):
        SkillStep(id="bad", type=StepType.PROMPT)  # missing `prompt`
    with pytest.raises(PydanticValidationError):
        SkillStep(id="bad2", type=StepType.SKILL)  # missing `skill`


def test_workflow_step_requires_matching_body():
    with pytest.raises(PydanticValidationError):
        WorkflowStep(id="bad", type=WorkflowStepType.SKILL)  # missing skill
    with pytest.raises(PydanticValidationError):
        WorkflowStep(id="bad", type=WorkflowStepType.PARALLEL)  # missing children


def test_competency_rejects_unknown_fields():
    with pytest.raises(PydanticValidationError):
        Competency(id="x", name="X", unknown_field="boom")  # type: ignore[call-arg]


def test_id_pattern_enforced():
    with pytest.raises(PydanticValidationError):
        Competency(id="Has Spaces!", name="X")


def test_policy_requires_at_least_one_pattern():
    with pytest.raises(PydanticValidationError):
        Policy(id="empty", name="Empty", effect=PolicyEffect.ALLOW, applies_to=[])


def test_default_workflow_falls_back_to_first():
    wf1 = Workflow(id="a", name="A", steps=[WorkflowStep(id="s", type=WorkflowStepType.SKILL, skill="x")])
    wf2 = Workflow(id="b", name="B", steps=[WorkflowStep(id="s", type=WorkflowStepType.SKILL, skill="x")])
    c = Competency(id="c", name="C", workflows=[wf1, wf2])
    assert c.default_workflow() is wf1
