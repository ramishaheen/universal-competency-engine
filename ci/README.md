# Enabling CI

This repo ships a complete GitHub Actions workflow (`ci/ci.yml.template`), but
it wasn't placed in `.github/workflows/` for the initial commit because the
OAuth token used for the first push lacked the `workflow` scope. To enable CI:

```bash
gh auth refresh -s workflow
mkdir -p .github/workflows
cp ci/ci.yml.template .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Enable GitHub Actions CI"
git push
```

The workflow runs (1) `ruff check`, (2) `pytest` across all packages, (3)
validates every sample competency YAML, and (4) builds the Next.js Studio.
