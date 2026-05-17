from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from uce_cli.main import app

runner = CliRunner()


def test_create_then_validate_then_inspect(tmp_path: Path):
    out = tmp_path / "comp.yaml"
    r = runner.invoke(
        app,
        ["create", "demo", "--name", "Demo", "--mission", "test", "--out", str(out)],
    )
    assert r.exit_code == 0, r.output
    assert out.exists()

    r = runner.invoke(app, ["validate", str(out)])
    assert r.exit_code == 0, r.output

    r = runner.invoke(app, ["inspect", str(out)])
    assert r.exit_code == 0, r.output
    assert "Demo" in r.output


def test_validate_flags_bad_file(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: bad\nname: Bad\nworkflows:\n  - id: w\n    name: W\n    steps:\n      - id: r\n        type: skill\n        skill: ghost\n",
        encoding="utf-8",
    )
    r = runner.invoke(app, ["validate", str(bad)])
    assert r.exit_code != 0
    assert "ghost" in r.output
