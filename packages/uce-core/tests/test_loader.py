"""Loader tests."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from uce_core import LoaderError, dump_competency, load_competency, load_competency_from_dict


YAML_GOOD = textwrap.dedent(
    """
    id: hello
    name: Hello Competency
    mission: Say hello in many ways
    objectives:
      - id: be_friendly
        name: Be friendly
    skills:
      - id: greet
        name: Greet
        execution_steps:
          - id: say
            type: prompt
            prompt: "Say hello to {{name}}"
    workflows:
      - id: main
        name: Main
        is_default: true
        steps:
          - id: greet_step
            type: skill
            skill: greet
    policies:
      - id: allow
        name: Allow All
        effect: allow
        applies_to: ["*"]
    llm:
      provider: anthropic
      model: claude-sonnet-4-6
    """
).strip()


def test_load_from_file(tmp_path: Path):
    p = tmp_path / "competency.yaml"
    p.write_text(YAML_GOOD, encoding="utf-8")
    c = load_competency(p)
    assert c.id == "hello"
    assert c.skill_by_id("greet") is not None


def test_load_missing_file_raises():
    with pytest.raises(LoaderError):
        load_competency("/nonexistent/path.yaml")


def test_load_empty_file_raises(tmp_path: Path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_competency(p)


def test_load_bad_yaml_raises(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("id: x\n  bad-indent:\n - oops", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_competency(p)


def test_load_non_mapping_raises(tmp_path: Path):
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(LoaderError):
        load_competency(p)


def test_load_from_dict_validation_wrapped():
    with pytest.raises(LoaderError):
        load_competency_from_dict({"id": "x"})  # missing required `name`


def test_dump_round_trip(tmp_path: Path):
    p = tmp_path / "in.yaml"
    p.write_text(YAML_GOOD, encoding="utf-8")
    c = load_competency(p)
    out = tmp_path / "out.yaml"
    text = dump_competency(c, out)
    assert "id: hello" in text
    assert out.exists()
    c2 = load_competency(out)
    assert c2.id == c.id
    assert len(c2.skills) == len(c.skills)
