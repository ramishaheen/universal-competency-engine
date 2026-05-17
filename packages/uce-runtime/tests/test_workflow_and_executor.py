"""End-to-end runtime tests using a fake LLM."""
from __future__ import annotations

import json

import pytest

from uce_core.models import (
    Competency,
    Objective,
    Policy,
    PolicyEffect,
    PriorityLevel,
    Skill,
    SkillStep,
    StepType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
)
from uce_runtime import (
    AuditLogger,
    CompetencyExecutor,
    MemoryStore,
    ToolRegistry,
)
from uce_runtime.context import RunStatus
from uce_runtime.policy import PolicyEffect as _PE


def _competency(skills, workflows, policies=None) -> Competency:
    return Competency(
        id="c",
        name="C",
        mission="test",
        objectives=[Objective(id="o", name="O")],
        skills=skills,
        workflows=workflows,
        policies=policies or [],
        priority_level=PriorityLevel.LOW,
    )


@pytest.mark.asyncio
async def test_simple_prompt_workflow_runs_end_to_end(fake_llm):
    skill = Skill(
        id="greet",
        name="Greet",
        execution_steps=[
            SkillStep(
                id="say",
                type=StepType.PROMPT,
                prompt="Say hi to {{inputs.name}}",
                output_key="greeting",
            )
        ],
    )
    wf = Workflow(
        id="main",
        name="Main",
        is_default=True,
        steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="greet", output_key="greeting")],
    )
    c = _competency([skill], [wf])
    ex = CompetencyExecutor(competency=c, llm=fake_llm)
    ctx, plan, ev = await ex.execute({"name": "Rami"}, run_plan=False)
    assert ctx.status == RunStatus.SUCCEEDED
    assert "echo: Say hi to Rami" in ctx.data["greeting"]
    assert ev.success is True
    assert ev.tokens_in > 0


@pytest.mark.asyncio
async def test_policy_denies_top_level_execute(fake_llm):
    skill = Skill(id="x", name="x", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="hi")])
    wf = Workflow(id="w", name="w", steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="x")])
    p = Policy(id="deny_run", name="Deny", effect=PolicyEffect.DENY, applies_to=["competency:c:execute"], reason="testing deny")
    c = _competency([skill], [wf], [p])
    ex = CompetencyExecutor(competency=c, llm=fake_llm)
    ctx, plan, ev = await ex.execute({}, run_plan=False)
    assert ctx.status == RunStatus.DENIED
    assert ev.success is False


@pytest.mark.asyncio
async def test_workflow_approval_suspends_run(fake_llm):
    skill = Skill(id="x", name="x", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="hi")])
    wf = Workflow(
        id="w",
        name="w",
        is_default=True,
        steps=[
            WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="x"),
            WorkflowStep(
                id="approve_step",
                type=WorkflowStepType.APPROVAL,
                approval_role="admin",
                approval_message="confirm before continuing",
            ),
            WorkflowStep(id="never", type=WorkflowStepType.SKILL, skill="x"),
        ],
    )
    c = _competency([skill], [wf])
    ex = CompetencyExecutor(competency=c, llm=fake_llm)
    ctx, plan, ev = await ex.execute({}, run_plan=False)
    assert ctx.status == RunStatus.PENDING_APPROVAL
    assert ctx.pending_approval is not None
    assert ctx.pending_approval["required_role"] == "admin"


@pytest.mark.asyncio
async def test_parallel_and_conditional_workflow(fake_llm):
    s1 = Skill(id="a", name="A", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="A")])
    s2 = Skill(id="b", name="B", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="B")])
    wf = Workflow(
        id="w",
        name="w",
        is_default=True,
        steps=[
            WorkflowStep(
                id="par",
                type=WorkflowStepType.PARALLEL,
                children=[
                    WorkflowStep(id="ra", type=WorkflowStepType.SKILL, skill="a", output_key="r_a"),
                    WorkflowStep(id="rb", type=WorkflowStepType.SKILL, skill="b", output_key="r_b"),
                ],
            ),
            WorkflowStep(
                id="cond",
                type=WorkflowStepType.CONDITIONAL,
                when="'A' in data.r_a",
                then=[WorkflowStep(id="t", type=WorkflowStepType.SKILL, skill="a", output_key="r_then")],
                otherwise=[WorkflowStep(id="o", type=WorkflowStepType.SKILL, skill="b", output_key="r_else")],
            ),
        ],
    )
    c = _competency([s1, s2], [wf])
    ex = CompetencyExecutor(competency=c, llm=fake_llm)
    ctx, _, _ = await ex.execute({}, run_plan=False)
    assert ctx.status == RunStatus.SUCCEEDED
    assert "r_a" in ctx.data and "r_b" in ctx.data
    assert "r_then" in ctx.data
    assert "r_else" not in ctx.data


@pytest.mark.asyncio
async def test_tool_registry_called(fake_llm):
    tools = ToolRegistry()
    captured: dict = {}

    async def my_tool(inputs):
        captured.update(inputs)
        return {"ok": True, "received": inputs}

    tools.register("my_tool", my_tool)

    skill = Skill(
        id="callit",
        name="Call",
        execution_steps=[
            SkillStep(
                id="t",
                type=StepType.TOOL,
                tool="my_tool",
                inputs={"name": "{{inputs.name}}", "fixed": "abc"},
                output_key="tool_out",
            )
        ],
    )
    wf = Workflow(
        id="w",
        name="w",
        is_default=True,
        steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="callit", output_key="tool_out")],
    )
    c = _competency([skill], [wf])
    ex = CompetencyExecutor(competency=c, llm=fake_llm, tools=tools)
    ctx, _, _ = await ex.execute({"name": "Rami"}, run_plan=False)
    assert ctx.status == RunStatus.SUCCEEDED
    assert captured == {"name": "Rami", "fixed": "abc"}


@pytest.mark.asyncio
async def test_reasoner_produces_plan_from_json(fake_llm_factory):
    plan_json = json.dumps(
        {
            "rationale": "Pick the right skill",
            "steps": [
                {"description": "say hello", "skill_id": "greet", "rationale": "matches goal", "expected_output": "greeting text"},
            ],
            "risk_score": 0.1,
            "confidence": 0.95,
            "alignment_score": 0.9,
            "requires_human_approval": False,
            "notes": ["clear case"],
        }
    )
    llm = fake_llm_factory(reply_fn=lambda _, __: plan_json)
    skill = Skill(id="greet", name="Greet", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="hi")])
    wf = Workflow(id="w", name="w", is_default=True, steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="greet")])
    c = _competency([skill], [wf])
    ex = CompetencyExecutor(competency=c, llm=llm)
    ctx, plan, _ = await ex.execute({}, goal="greet the user")
    assert plan is not None
    assert plan.confidence == pytest.approx(0.95)
    assert plan.steps[0].skill_id == "greet"
    assert ctx.status == RunStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_episodic_memory_written_on_success(fake_llm):
    skill = Skill(id="x", name="x", execution_steps=[SkillStep(id="s", type=StepType.PROMPT, prompt="hi")])
    wf = Workflow(id="w", name="w", is_default=True, steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="x")])
    c = _competency([skill], [wf])
    mem = MemoryStore()
    ex = CompetencyExecutor(competency=c, llm=fake_llm, memory=mem)
    await ex.execute({}, run_plan=False)
    from uce_core.models import MemoryType

    eps = mem.recall(competency_id="c", types=[MemoryType.EPISODIC])
    assert len(eps) == 1
    assert "completed with status=succeeded" in eps[0].content


@pytest.mark.asyncio
async def test_skill_retry_and_fallback(fake_llm):
    # Build a tool that fails twice, then succeeds — should be invoked 2 retries deep.
    tools = ToolRegistry()
    call_count = {"n": 0}

    async def flaky(_):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError("flake")
        return {"ok": True}

    tools.register("flaky", flaky)
    from uce_core.models import ErrorHandling

    skill = Skill(
        id="ft",
        name="FT",
        execution_steps=[
            SkillStep(
                id="t",
                type=StepType.TOOL,
                tool="flaky",
                error_handling=ErrorHandling(retry_count=2, retry_backoff_seconds=0),
            )
        ],
    )
    wf = Workflow(id="w", name="w", is_default=True, steps=[WorkflowStep(id="r", type=WorkflowStepType.SKILL, skill="ft")])
    c = _competency([skill], [wf])
    ex = CompetencyExecutor(competency=c, llm=fake_llm, tools=tools)
    ctx, _, _ = await ex.execute({}, run_plan=False)
    assert ctx.status == RunStatus.SUCCEEDED
    assert call_count["n"] == 3
