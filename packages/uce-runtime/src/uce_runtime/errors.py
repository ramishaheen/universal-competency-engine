"""Runtime exception hierarchy."""
from __future__ import annotations


class RuntimeError(Exception):
    """Base for all runtime exceptions."""


class PolicyDenied(RuntimeError):
    """Raised when a policy denies an action."""

    def __init__(self, action: str, reason: str, policy_id: str | None = None) -> None:
        super().__init__(f"Policy denied action '{action}': {reason}")
        self.action = action
        self.reason = reason
        self.policy_id = policy_id


class PolicyRequiresApproval(RuntimeError):
    """Raised when a policy requires human approval before proceeding."""

    def __init__(self, action: str, required_role: str, policy_id: str | None = None) -> None:
        super().__init__(f"Policy requires approval by '{required_role}' for '{action}'")
        self.action = action
        self.required_role = required_role
        self.policy_id = policy_id


class ToolNotFound(RuntimeError):
    """Raised when a skill references a tool that hasn't been registered."""


class ExecutionError(RuntimeError):
    """Raised when execution of a step fails after retries/fallbacks."""

    def __init__(self, step_id: str, message: str, cause: Exception | None = None) -> None:
        super().__init__(f"Step '{step_id}' failed: {message}")
        self.step_id = step_id
        self.cause = cause
