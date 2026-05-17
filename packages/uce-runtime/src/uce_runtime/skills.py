"""Skill executor + tool registry.

A skill is a sequence of `SkillStep`s. Each step is one of:
- prompt  → LLM completion (templated with Jinja2 over the run context)
- tool    → call a registered tool with rendered inputs
- python  → call a registered python callable (`module:function` form)
- skill   → invoke another skill in the same competency
- http    → arbitrary HTTP request

Steps may have a `when` condition (skipped if falsy) and `output_key` (writes the
step's result into `ctx.data[output_key]`). Step `inputs` are dicts where every
string value is Jinja-rendered against the run context.
"""
from __future__ import annotations

import asyncio
import importlib
import json
from typing import Any, Awaitable, Callable

import httpx
from jinja2 import Environment, StrictUndefined, TemplateError

from uce_core.models import Competency, Skill, SkillStep, StepType
from uce_llm.base import LLMProvider, Message, Role

from uce_runtime.context import RunContext
from uce_runtime.errors import ExecutionError, ToolNotFound
from uce_runtime.expressions import safe_eval

Tool = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ToolRegistry:
    """Maps tool name → async callable. Callers register their own tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, fn: Tool) -> None:
        self._tools[name] = fn

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolNotFound(f"tool '{name}' is not registered")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def has(self, name: str) -> bool:
        return name in self._tools


def register_builtin_tools(registry: ToolRegistry) -> None:
    """Register http_get, http_post, json_extract — useful defaults."""

    async def http_get(inputs: dict[str, Any]) -> dict[str, Any]:
        url = inputs["url"]
        headers = inputs.get("headers") or {}
        params = inputs.get("params") or {}
        timeout = float(inputs.get("timeout", 30))
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(url, headers=headers, params=params)
        return {"status": r.status_code, "body": _maybe_json(r.text), "headers": dict(r.headers)}

    async def http_post(inputs: dict[str, Any]) -> dict[str, Any]:
        url = inputs["url"]
        headers = inputs.get("headers") or {}
        json_body = inputs.get("json")
        data = inputs.get("data")
        timeout = float(inputs.get("timeout", 30))
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(url, headers=headers, json=json_body, data=data)
        return {"status": r.status_code, "body": _maybe_json(r.text), "headers": dict(r.headers)}

    async def json_extract(inputs: dict[str, Any]) -> dict[str, Any]:
        source = inputs["source"]
        path = inputs["path"]  # dotted path e.g. "data.items.0.name"
        current: Any = json.loads(source) if isinstance(source, str) else source
        for part in path.split("."):
            if isinstance(current, list):
                current = current[int(part)]
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                current = None
            if current is None:
                break
        return {"value": current}

    registry.register("http_get", http_get)
    registry.register("http_post", http_post)
    registry.register("json_extract", json_extract)


def _maybe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class SkillExecutor:
    """Executes a `Skill` end-to-end against a `RunContext`."""

    def __init__(
        self,
        *,
        competency: Competency,
        llm: LLMProvider,
        tools: ToolRegistry,
    ) -> None:
        self.competency = competency
        self.llm = llm
        self.tools = tools
        self._jinja = Environment(undefined=StrictUndefined, autoescape=False)

    async def run(self, skill: Skill, ctx: RunContext, inputs: dict[str, Any] | None = None) -> Any:
        """Execute every step in order, returning the final step's output (or last assigned key)."""
        local_inputs = dict(inputs or {})
        skill_data: dict[str, Any] = {"inputs": local_inputs, "outputs": {}}
        last_output: Any = None
        for step in skill.execution_steps:
            if step.when:
                cond_ctx = ctx.eval_context() | {"skill_inputs": local_inputs, "step_outputs": skill_data["outputs"]}
                try:
                    if not bool(safe_eval(step.when, cond_ctx)):
                        continue
                except Exception as e:  # noqa: BLE001
                    raise ExecutionError(step.id, f"`when` evaluation failed: {e}", cause=e) from e
            result = await self._run_step(step, ctx, skill_data)
            skill_data["outputs"][step.id] = result
            if step.output_key:
                ctx.data[step.output_key] = result
            last_output = result

        ctx.skill_results[skill.id] = last_output if last_output is not None else skill_data["outputs"]
        return ctx.skill_results[skill.id]

    async def _run_step(self, step: SkillStep, ctx: RunContext, skill_data: dict[str, Any]) -> Any:
        rendered_inputs = self._render_inputs(step.inputs, ctx, skill_data)
        attempts = step.error_handling.retry_count + 1
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                return await self._dispatch(step, ctx, rendered_inputs)
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if attempt + 1 < attempts:
                    await asyncio.sleep(step.error_handling.retry_backoff_seconds * (attempt + 1))
                    continue
                break
        # All retries exhausted
        if step.error_handling.on_error == "skip":
            return None
        if step.error_handling.on_error == "fallback" and step.error_handling.fallback_skill:
            fb_skill = self.competency.skill_by_id(step.error_handling.fallback_skill)
            if fb_skill is None:
                raise ExecutionError(step.id, f"unknown fallback skill '{step.error_handling.fallback_skill}'")
            return await self.run(fb_skill, ctx, rendered_inputs)
        raise ExecutionError(step.id, str(last_exc), cause=last_exc) from last_exc

    async def _dispatch(self, step: SkillStep, ctx: RunContext, rendered_inputs: dict[str, Any]) -> Any:
        match step.type:
            case StepType.PROMPT:
                prompt = self._render(step.prompt or "", ctx, rendered_inputs)
                resp = await self.llm.complete([Message(role=Role.USER, content=prompt)])
                ctx.add_usage(resp.usage)
                return resp.text
            case StepType.TOOL:
                tool = self.tools.get(step.tool or "")
                return await tool(rendered_inputs)
            case StepType.PYTHON:
                mod_name, _, func_name = (step.python_callable or "").partition(":")
                if not mod_name or not func_name:
                    raise ExecutionError(step.id, "python_callable must be 'module:function'")
                module = importlib.import_module(mod_name)
                fn = getattr(module, func_name)
                if asyncio.iscoroutinefunction(fn):
                    return await fn(rendered_inputs)
                return fn(rendered_inputs)
            case StepType.SKILL:
                sub = self.competency.skill_by_id(step.skill or "")
                if sub is None:
                    raise ExecutionError(step.id, f"unknown sub-skill '{step.skill}'")
                return await self.run(sub, ctx, rendered_inputs)
            case StepType.HTTP:
                http_cfg = step.http or {}
                method = (http_cfg.get("method") or "GET").upper()
                tool_inputs = {**http_cfg, **rendered_inputs}
                if method == "GET":
                    return await self.tools.get("http_get")(tool_inputs)
                if method == "POST":
                    return await self.tools.get("http_post")(tool_inputs)
                raise ExecutionError(step.id, f"unsupported HTTP method: {method}")
            case _:
                raise ExecutionError(step.id, f"unsupported step type: {step.type}")

    def _render(self, template: str, ctx: RunContext, extra: dict[str, Any] | None = None) -> str:
        try:
            tmpl = self._jinja.from_string(template)
            return tmpl.render(**(ctx.eval_context() | (extra or {})))
        except TemplateError as e:
            raise ExecutionError("(template)", f"Jinja error: {e}", cause=e) from e

    def _render_inputs(self, inputs: dict[str, Any], ctx: RunContext, skill_data: dict[str, Any]) -> dict[str, Any]:
        rendered: dict[str, Any] = {}
        for k, v in (inputs or {}).items():
            if isinstance(v, str):
                rendered[k] = self._render(v, ctx, {"skill_inputs": skill_data.get("inputs", {})})
            else:
                rendered[k] = v
        return rendered
