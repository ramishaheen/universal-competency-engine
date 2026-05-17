# Implementation Plan — UCE v0.1

Build order (each step is independently testable):

1. **uce-core** — schema + loader + validator + tests
2. **uce-llm** — base ABC + Anthropic + OpenAI + Ollama + registry + tests (mocked)
3. **uce-runtime** — memory, policy, reasoner, workflow, executor, audit, evaluator + tests
4. **uce-cli** — `competency create/validate/run/serve`
5. **uce-api** — DB models, Alembic, auth, routers, RBAC + tests
6. **competencies/procurement** — full sample
7. **competencies/{legal-review,cybersecurity,hr-screening}** — stubs
8. **apps/studio** — Next.js, auth, list/create/run, audit, perf
9. **docker/, scripts/, CI** — Dockerfile, docker-compose, GH Actions
10. **README + CONTRIBUTING + CHANGELOG**
11. **Smoke test** — validate procurement YAML, run via runtime (Anthropic), hit API
12. **`gh repo create --push`** — publish to GitHub
13. **Completion report** in user's exact format

Acceptance criteria for v0.1:
- `pytest -q` passes across all packages.
- `uvicorn uce_api.main:app` boots and `/health` returns 200.
- `pnpm dev` (or `npm run dev`) boots the Studio.
- `competency run competencies/procurement --input '{...}'` produces a real LLM-backed plan with audit trail.
- `docker compose up` brings up API + Studio + SQLite volume.
- README explains: install, run, create your own competency, deploy.
