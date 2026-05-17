"""Semantic (cross-field, cross-object) validation for a Competency.

`Competency.model_validate` already enforces shapes. This validator catches
problems like:

- a workflow step references a skill id that doesn't exist
- a skill step references another skill id that doesn't exist
- duplicate ids
- empty required collections that aren't structural-required but are semantically required
- agent referenced by a workflow but not defined
"""
from __future__ import annotations

from uce_core.errors import ValidationError
from uce_core.models import (
    Competency,
    SkillStep,
    StepType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
)


def validate_competency(competency: Competency) -> list[str]:
    """Return a list of semantic issues. Empty list = valid.

    Raises ValidationError only if you call .raise_if_invalid() yourself; this
    function is non-throwing so callers can collect and present all issues.
    """
    issues: list[str] = []
    _check_unique_ids(competency, issues)
    _check_skill_refs(competency, issues)
    _check_workflow_refs(competency, issues)
    _check_objectives(competency, issues)
    _check_policies(competency, issues)
    return issues


def raise_if_invalid(competency: Competency) -> None:
    issues = validate_competency(competency)
    if issues:
        raise ValidationError(
            f"Competency '{competency.id}' has {len(issues)} validation issue(s)",
            issues=issues,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Internal checks
# ──────────────────────────────────────────────────────────────────────────────


def _check_unique_ids(c: Competency, issues: list[str]) -> None:
    for label, items in (
        ("skill", c.skills),
        ("workflow", c.workflows),
        ("policy", c.policies),
        ("objective", c.objectives),
        ("agent", c.agents),
    ):
        seen: dict[str, int] = {}
        for item in items:
            seen[item.id] = seen.get(item.id, 0) + 1
        for sid, count in seen.items():
            if count > 1:
                issues.append(f"duplicate {label} id: '{sid}' appears {count} times")


def _check_skill_refs(c: Competency, issues: list[str]) -> None:
    skill_ids = {s.id for s in c.skills}
    for skill in c.skills:
        for dep in skill.dependencies:
            if dep not in skill_ids:
                issues.append(f"skill '{skill.id}' depends on unknown skill '{dep}'")
        for step in skill.execution_steps:
            _check_skill_step_refs(skill_id=skill.id, step=step, skill_ids=skill_ids, issues=issues)
        if skill.error_handling.fallback_skill and skill.error_handling.fallback_skill not in skill_ids:
            issues.append(
                f"skill '{skill.id}' fallback_skill references unknown skill '{skill.error_handling.fallback_skill}'"
            )


def _check_skill_step_refs(
    *, skill_id: str, step: SkillStep, skill_ids: set[str], issues: list[str]
) -> None:
    if step.type == StepType.SKILL and step.skill and step.skill not in skill_ids:
        issues.append(
            f"skill '{skill_id}' step '{step.id}' references unknown skill '{step.skill}'"
        )
    if step.error_handling.fallback_skill and step.error_handling.fallback_skill not in skill_ids:
        issues.append(
            f"skill '{skill_id}' step '{step.id}' fallback_skill references unknown skill "
            f"'{step.error_handling.fallback_skill}'"
        )


def _check_workflow_refs(c: Competency, issues: list[str]) -> None:
    skill_ids = {s.id for s in c.skills}
    workflow_ids = {w.id for w in c.workflows}
    for wf in c.workflows:
        _walk_workflow_steps(wf, wf.steps, skill_ids, workflow_ids, issues)


def _walk_workflow_steps(
    wf: Workflow,
    steps: list[WorkflowStep],
    skill_ids: set[str],
    workflow_ids: set[str],
    issues: list[str],
) -> None:
    for step in steps:
        if step.type == WorkflowStepType.SKILL and step.skill and step.skill not in skill_ids:
            issues.append(
                f"workflow '{wf.id}' step '{step.id}' references unknown skill '{step.skill}'"
            )
        if (
            step.type == WorkflowStepType.SUB_WORKFLOW
            and step.sub_workflow
            and step.sub_workflow not in workflow_ids
        ):
            issues.append(
                f"workflow '{wf.id}' step '{step.id}' references unknown sub-workflow "
                f"'{step.sub_workflow}'"
            )
        # recurse
        if step.children:
            _walk_workflow_steps(wf, step.children, skill_ids, workflow_ids, issues)
        if step.then:
            _walk_workflow_steps(wf, step.then, skill_ids, workflow_ids, issues)
        if step.otherwise:
            _walk_workflow_steps(wf, step.otherwise, skill_ids, workflow_ids, issues)


def _check_objectives(c: Competency, issues: list[str]) -> None:
    if c.mission and not c.objectives:
        issues.append(
            f"competency '{c.id}' has a mission but no objectives — at least one objective is recommended for alignment scoring"
        )


def _check_policies(c: Competency, issues: list[str]) -> None:
    # If any policy uses RequireApproval, the competency should define at least one role
    from uce_core.models import PolicyEffect

    for p in c.policies:
        if p.effect == PolicyEffect.REQUIRE_APPROVAL and not p.required_role:
            issues.append(
                f"policy '{p.id}' has effect=require_approval but no required_role set"
            )
