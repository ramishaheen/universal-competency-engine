# Contributing

Thanks for your interest in UCE.

## Dev setup

```bash
uv sync --all-packages
uv run pytest -q                          # all backend tests
cd apps/studio && npm install && npm run build  # frontend
```

## Conventions

- All code is type-checked: Python uses `pydantic` v2 + `mypy`-compatible style; TS is `strict`.
- Public Python APIs have docstrings; cross-package symbols are re-exported from each package's `__init__.py`.
- New runtime features ship with tests in the same package.
- Schema changes go through `uce-core` first; runtime / api / cli adapt downstream.

## Pull requests

- One concern per PR.
- Tests must pass: `uv run pytest -q` and `npm --prefix apps/studio run build`.
- Bump versions in the relevant package's `pyproject.toml` if API-breaking.

## Reporting bugs

Open a GitHub issue with a minimal reproduction (YAML competency + how you ran it + observed vs expected).
