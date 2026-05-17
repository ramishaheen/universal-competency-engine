# Changelog

## 0.1.0 — 2026-05-17

Initial public release.

- `uce-core` — Competency / Skill / Workflow / Policy / Memory / Objective / Agent schema, YAML loader, semantic validator.
- `uce-runtime` — Reasoning, workflow orchestration (sequential / parallel / conditional / approval / sub-workflow / escalation), policy engine (allow / deny / require_approval), nine memory types, audit logger with secret redaction, evaluator.
- `uce-llm` — Anthropic, OpenAI, Ollama provider adapters; pluggable registry.
- `uce-api` — FastAPI server, SQLAlchemy persistence (SQLite default, Postgres-compatible), JWT auth, RBAC (admin / author / operator / viewer), all spec endpoints.
- `uce-cli` — `competency create | validate | inspect | run | serve`.
- `apps/studio` — Next.js 15 + Tailwind UI: list / create / run competencies, view executions + audit + performance.
- `competencies/procurement` — full sample. Stubs for legal-review, cybersecurity, hr-screening.
- Docker + docker-compose + GitHub Actions CI.
