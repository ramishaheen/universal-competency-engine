"""YAML <-> Competency loader."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from uce_core.errors import LoaderError
from uce_core.models import Competency


def load_competency(path: str | Path) -> Competency:
    """Load and validate a Competency from a YAML file path."""
    p = Path(path)
    if not p.exists():
        raise LoaderError(f"Competency file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise LoaderError(f"YAML parse error in {p}: {e}") from e
    if raw is None:
        raise LoaderError(f"Competency file is empty: {p}")
    if not isinstance(raw, dict):
        raise LoaderError(f"Competency file root must be a mapping, got {type(raw).__name__}: {p}")
    return load_competency_from_dict(raw, source=str(p))


def load_competency_from_dict(data: dict[str, Any], source: str = "<dict>") -> Competency:
    """Build a Competency from an already-parsed dict.

    Wraps pydantic.ValidationError in our LoaderError for a clean message.
    """
    try:
        return Competency.model_validate(data)
    except PydanticValidationError as e:
        raise LoaderError(f"Invalid competency definition ({source}):\n{e}") from e


def dump_competency(competency: Competency, path: str | Path | None = None) -> str:
    """Serialize a Competency to YAML. Writes to `path` if provided; always returns the string."""
    data = competency.model_dump(mode="json", exclude_none=False)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text
