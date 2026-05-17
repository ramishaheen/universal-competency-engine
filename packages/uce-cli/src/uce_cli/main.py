"""`competency` CLI — create / validate / run / serve."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from uce_core import dump_competency, load_competency, validate_competency
from uce_core.errors import LoaderError
from uce_core.models import (
    Competency,
    LLMConfig,
    Objective,
    Policy,
    PolicyEffect,
    Skill,
    SkillStep,
    StepType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
)
from uce_llm.registry import build_provider
from uce_runtime import AuditLogger, CompetencyExecutor, MemoryStore

app = typer.Typer(help="Universal Competency Engine — author, validate, and run competencies.")
console = Console()


# ── create ───────────────────────────────────────────────────────────────────


@app.command()
def create(
    competency_id: str = typer.Argument(..., help="Lowercase id, e.g. 'procurement'"),
    out: Path = typer.Option(Path("competency.yaml"), "--out", "-o", help="Output YAML path"),
    name: str = typer.Option(..., "--name", "-n", help="Human-readable name"),
    mission: str = typer.Option("", "--mission", "-m", help="Mission statement"),
    domain: str = typer.Option("", "--domain", "-d", help="Domain (e.g. 'procurement')"),
    provider: str = typer.Option("anthropic", "--provider", help="LLM provider"),
    model: str = typer.Option("claude-sonnet-4-6", "--model"),
) -> None:
    """Scaffold a starter Competency YAML."""
    if out.exists():
        console.print(f"[red]refusing to overwrite[/red] {out}")
        raise typer.Exit(2)

    c = Competency(
        id=competency_id,
        name=name,
        mission=mission,
        domain=domain,
        objectives=[Objective(id="primary", name="Primary objective", description="Describe me")],
        skills=[
            Skill(
                id="example_skill",
                name="Example Skill",
                description="Replace me with a real skill",
                execution_steps=[
                    SkillStep(
                        id="step_1",
                        type=StepType.PROMPT,
                        prompt="Given inputs: {{ inputs }}, produce a useful response.",
                        output_key="example_output",
                    )
                ],
            )
        ],
        workflows=[
            Workflow(
                id="main",
                name="Main",
                is_default=True,
                steps=[
                    WorkflowStep(
                        id="run_example",
                        type=WorkflowStepType.SKILL,
                        skill="example_skill",
                        output_key="example_output",
                    )
                ],
            )
        ],
        policies=[
            Policy(
                id="allow_all",
                name="Allow all",
                effect=PolicyEffect.ALLOW,
                applies_to=["*"],
                reason="default",
            )
        ],
        llm=LLMConfig(provider=provider, model=model),
    )
    dump_competency(c, out)
    console.print(f"[green]created[/green] {out}")


# ── validate ─────────────────────────────────────────────────────────────────


@app.command()
def validate(path: Path = typer.Argument(..., exists=True)) -> None:
    """Validate a competency YAML (shape + semantic)."""
    try:
        c = load_competency(path)
    except LoaderError as e:
        console.print(f"[red]✗ schema error[/red]\n{e}")
        raise typer.Exit(1)
    issues = validate_competency(c)
    if not issues:
        console.print(f"[green]✓ valid[/green] — '{c.id}' ({len(c.skills)} skills, {len(c.workflows)} workflows)")
        return
    console.print(f"[red]✗ {len(issues)} issue(s) found:[/red]")
    for i in issues:
        console.print(f"  - {i}")
    raise typer.Exit(1)


# ── inspect ──────────────────────────────────────────────────────────────────


@app.command()
def inspect(path: Path = typer.Argument(..., exists=True)) -> None:
    """Show a summary table of a competency."""
    c = load_competency(path)
    t = Table(title=f"Competency: {c.name} ({c.id} v{c.version})")
    t.add_column("Field", style="bold")
    t.add_column("Value")
    t.add_row("Mission", c.mission or "—")
    t.add_row("Domain", c.domain or "—")
    t.add_row("Risk", c.risk_level.value)
    t.add_row("Priority", c.priority_level.value)
    t.add_row("Skills", str(len(c.skills)))
    t.add_row("Workflows", str(len(c.workflows)))
    t.add_row("Policies", str(len(c.policies)))
    t.add_row("Objectives", str(len(c.objectives)))
    t.add_row("LLM", f"{c.llm.provider}:{c.llm.model}")
    console.print(t)

    if c.skills:
        st = Table(title="Skills")
        st.add_column("id")
        st.add_column("name")
        st.add_column("steps")
        for s in c.skills:
            st.add_row(s.id, s.name, str(len(s.execution_steps)))
        console.print(st)


# ── run ──────────────────────────────────────────────────────────────────────


@app.command()
def run(
    path: Path = typer.Argument(..., exists=True, help="Competency YAML"),
    inputs: str = typer.Option("{}", "--inputs", "-i", help="JSON object of inputs"),
    goal: str | None = typer.Option(None, "--goal"),
    workflow_id: str | None = typer.Option(None, "--workflow"),
    no_plan: bool = typer.Option(False, "--no-plan", help="Skip the reasoning step"),
    actor_id: str = typer.Option("cli", "--actor"),
    role: list[str] = typer.Option(["operator"], "--role"),
    pretty: bool = typer.Option(True, "--pretty/--json"),
) -> None:
    """Execute a competency locally (no API required)."""
    c = load_competency(path)
    issues = validate_competency(c)
    if issues:
        console.print(f"[red]✗ validation failed:[/red]")
        for i in issues:
            console.print(f"  - {i}")
        raise typer.Exit(1)

    parsed_inputs: dict[str, Any] = json.loads(inputs)
    llm = build_provider(
        provider=c.llm.provider,
        model=c.llm.model,
        base_url=c.llm.base_url,
        temperature=c.llm.temperature,
        max_tokens=c.llm.max_tokens,
    )
    ex = CompetencyExecutor(competency=c, llm=llm, memory=MemoryStore(), audit=AuditLogger())
    ctx, plan, ev = asyncio.run(
        ex.execute(
            inputs=parsed_inputs,
            actor={"id": actor_id, "roles": role},
            workflow_id=workflow_id,
            goal=goal,
            run_plan=not no_plan,
        )
    )
    result = {
        "status": ctx.status.value,
        "run_id": ctx.run_id,
        "outputs": ctx.outputs,
        "error": ctx.error,
        "pending_approval": ctx.pending_approval,
        "usage": {
            "tokens_in": ctx.usage.prompt_tokens,
            "tokens_out": ctx.usage.completion_tokens,
            "cost_usd": ctx.usage.cost_usd,
        },
        "evaluation": ev.to_dict(),
        "plan": _plan_summary(plan),
    }
    if pretty:
        console.print_json(json.dumps(result, default=str))
    else:
        sys.stdout.write(json.dumps(result, default=str) + "\n")


def _plan_summary(plan) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        "confidence": plan.confidence,
        "risk_score": plan.risk_score,
        "alignment_score": plan.alignment_score,
        "requires_human_approval": plan.requires_human_approval,
        "step_count": len(plan.steps),
        "rationale_preview": (plan.rationale or "")[:200],
    }


# ── serve ────────────────────────────────────────────────────────────────────


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run("uce_api.main:app", host=host, port=port, reload=reload, factory=False)


if __name__ == "__main__":
    app()
