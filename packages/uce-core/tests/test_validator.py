"""Semantic validator tests."""
from __future__ import annotations

import pytest

from uce_core import (
    Competency,
    Objective,
    Policy,
    PolicyEffect,
    Skill,
    SkillStep,
    StepType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
    validate_competency,
)
from uce_core.errors import ValidationError
from uce_core.validator import raise_if_invalid


def _skill(id_: str, dependencies: list[str] | None = None) -> Skill:
    return Skill(
        id=id_,
        name=id_.title(),
        dependencies=dependencies or [],
        execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="ok")],
    )


def test_valid_competency_has_no_issues():
    c = Competency(
        id="ok",
        name="OK",
        mission="x",
        objectives=[Objective(id="o1", name="O1")],
        skills=[_skill("a"), _skill("b", dependencies=["a"])],
        workflows=[
            Workflow(
                id="main",
                name="Main",
                steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="a")],
            )
        ],
    )
    assert validate_competency(c) == []


def test_unknown_skill_dependency_flagged():
    c = Competency(id="c", name="C", skills=[_skill("a", dependencies=["nope"])])
    issues = validate_competency(c)
    assert any("unknown skill 'nope'" in i for i in issues)


def test_workflow_referencing_unknown_skill_flagged():
    wf = Workflow(
        id="w",
        name="W",
        steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="ghost")],
    )
    c = Competency(id="c", name="C", workflows=[wf])
    issues = validate_competency(c)
    assert any("unknown skill 'ghost'" in i for i in issues)


def test_duplicate_skill_ids_flagged():
    c = Competency(id="c", name="C", skills=[_skill("dup"), _skill("dup")])
    issues = validate_competency(c)
    assert any("duplicate skill id" in i for i in issues)


def test_require_approval_without_role_flagged():
    p = Policy(id="p", name="P", effect=PolicyEffect.REQUIRE_APPROVAL)
    c = Competency(id="c", name="C", policies=[p])
    issues = validate_competency(c)
    assert any("require_approval" in i and "no required_role" in i for i in issues)


def test_mission_without_objectives_flagged():
    c = Competency(id="c", name="C", mission="do things")
    issues = validate_competency(c)
    assert any("at least one objective" in i for i in issues)


def test_raise_if_invalid_raises_on_problems():
    c = Competency(id="c", name="C", skills=[_skill("dup"), _skill("dup")])
    with pytest.raises(ValidationError) as exc:
        raise_if_invalid(c)
    assert "duplicate skill id" in str(exc.value)


def test_nested_workflow_validation():
    wf = Workflow(
        id="w",
        name="W",
        steps=[
            WorkflowStep(
                id="par",
                type=WorkflowStepType.PARALLEL,
                children=[
                    WorkflowStep(id="a", type=WorkflowStepType.SKILL, skill="ghost"),
                ],
            )
        ],
    )
    c = Competency(id="c", name="C", workflows=[wf])
    issues = validate_competency(c)
    assert any("unknown skill 'ghost'" in i for i in issues)
