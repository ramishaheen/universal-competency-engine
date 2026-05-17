"""Exception hierarchy for uce-core."""
from __future__ import annotations


class CompetencyError(Exception):
    """Base class for all UCE core errors."""


class LoaderError(CompetencyError):
    """Raised when a YAML file cannot be read or parsed."""


class ValidationError(CompetencyError):
    """Raised when a competency definition fails semantic validation.

    Pydantic raises its own `pydantic.ValidationError` for shape mismatches;
    this class is for cross-field, cross-object validation (e.g. a workflow
    referencing a skill id that doesn't exist).
    """

    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []

    def __str__(self) -> str:  # pragma: no cover - trivial
        if not self.issues:
            return super().__str__()
        joined = "\n  - ".join(self.issues)
        return f"{super().__str__()}\n  - {joined}"
