# Universal Competency Engine (UCE)

> Turn AI agents from task executors into **integrated expert competencies** that reason, remember, govern themselves, learn, and execute toward strategic objectives.

A **Competency** is not a single agent, not a single skill, and not just a workflow. It is an integrated, reusable expert capability composed of:

- **Skills** — atomic capabilities (prompts, tools, sub-skills, HTTP calls)
- **Reasoning** — plan-before-act with risk / confidence / alignment scoring
- **Workflows** — sequential / parallel / conditional / approval / sub-workflow / escalation
- **Memory** — short-term, long-term, episodic, semantic, procedural, policy, decision, user-preference, organisational
- **Policies** — `allow` / `deny` / `require_approval`, glob action patterns, condition expressions, RBAC
- **Objectives & governance** — every action is scored against mission alignment
- **Evaluation & audit** — every step is observable, every decision is logged

This repo ships:
- a Python **schema + SDK**
- a **runtime engine** (reasoning, workflow, memory, policy, executor, audit, evaluation)
- provider-agnostic **LLM adapters** (Anthropic / OpenAI / Ollama)
- a **REST API** with JWT auth + RBAC
- a **CLI** (`competency create|validate|inspect|run|serve`)
- a **Next.js Studio** for authoring, running, and inspecting competencies
- a **Procurement** sample competency (fully built) + 3 stubs (Legal-Review, Cybersecurity, HR-Screening)
- **Docker** + **CI** so it ships

---

## Quick start

### 1. Clone & install (Python)

```bash
git clone https://github.com/<you>/universal-competency-engine.git
cd universal-competency-engine
uv sync --all-packages
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY, or run an Ollama server
```

### 2. Run a competency from the CLI

```bash
uv run competency validate competencies/procurement/competency.yaml
uv run competency run competencies/procurement/competency.yaml \
  --inputs '{"request": "Buy 25 monitors for the design team", "budget_usd": 12000}'
```

### 3. Start the API + Studio

```bash
# Terminal 1 — API
uv run uvicorn uce_api.main:app --reload
# → http://localhost:8000/docs (OpenAPI/Swagger UI)
# → Default admin: admin@example.com / changeme  (override via UCE_BOOTSTRAP_ADMIN_PASSWORD)

# Terminal 2 — Studio
cd apps/studio
npm install
cp .env.example .env.local
npm run dev
# → http://localhost:3000
```

### 4. Or just `docker compose up`

```bash
docker compose up --build
# API → http://localhost:8000   Studio → http://localhost:3000
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                 Studio (Next.js 15 + Tailwind)                 │
└────────────────────────────────────────────────────────────────┘
                                  │  REST/JSON (JWT)
                                  ▼
┌────────────────────────────────────────────────────────────────┐
│                    uce-api (FastAPI + SQLAlchemy)              │
│        auth · RBAC · routers · persistence · audit             │
└──────────────────────────────────┬─────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────┐
│                          uce-runtime                           │
│   executor → policy → reasoner → workflow → skills → memory    │
│                  audit · evaluator (every step)                │
└────────────────┬────────────────────────────┬──────────────────┘
                 │                            │
                 ▼                            ▼
┌──────────────────────────┐    ┌────────────────────────────────┐
│ uce-llm                  │    │ uce-core                       │
│ Anthropic │ OpenAI │ Ollama │  │ schema · loader · validator    │
└──────────────────────────┘    └────────────────────────────────┘
```

The **execution flow** (matches the 19-section spec):

```
Request → Router → load(competency) → retrieve(memory) → policy.check
  → reasoner.plan → workflow.execute → validate → governance.review
  → respond → memory.update → audit.log → evaluator.score
```

---

## Repo layout

```
.
├─ packages/
│   ├─ uce-core/      # schema + YAML loader + semantic validator
│   ├─ uce-runtime/   # reasoning, workflow, memory, policy, executor, audit, eval
│   ├─ uce-llm/       # provider-agnostic adapters (Anthropic / OpenAI / Ollama)
│   ├─ uce-api/       # FastAPI server (auth, RBAC, all endpoints, SQLAlchemy)
│   └─ uce-cli/       # `competency` CLI
├─ apps/
│   └─ studio/        # Next.js 15 + Tailwind UI
├─ competencies/
│   ├─ procurement/   # fully implemented sample
│   ├─ legal-review/  # stub
│   ├─ cybersecurity/ # stub
│   └─ hr-screening/  # stub
├─ docker/            # Dockerfile.api · Dockerfile.studio · entrypoints
├─ docker-compose.yml
├─ docs/              # DESIGN.md, IMPLEMENTATION_PLAN.md, API.md
├─ examples/          # Python & curl example scripts
└─ scripts/           # dev convenience scripts
```

---

## Authoring a competency

A competency is a single YAML file. Minimal example:

```yaml
id: hello
name: Hello Competency
mission: Say hello to people
objectives:
  - id: be_friendly
    name: Be friendly
skills:
  - id: greet
    name: Greet
    execution_steps:
      - id: say
        type: prompt
        prompt: "Say hello to {{ inputs.name }}"
        output_key: greeting
workflows:
  - id: main
    name: Main
    is_default: true
    steps:
      - id: greet_step
        type: skill
        skill: greet
        output_key: greeting
policies:
  - id: allow
    name: Allow all
    effect: allow
    applies_to: ["*"]
llm:
  provider: anthropic
  model: claude-sonnet-4-6
```

Run it:

```bash
uv run competency run hello.yaml --inputs '{"name": "Rami"}'
```

See `competencies/procurement/competency.yaml` for a full example covering every layer:
skills, dependencies, parallel + conditional + approval workflow steps,
allow / deny / require_approval policies, agents, memory config, evaluation.

---

## REST API (selection)

All endpoints require JWT (`Authorization: Bearer <token>`) except `/health`, `/auth/login`, `/auth/register`.

| Verb | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Get a JWT |
| POST | `/auth/register` | Self-register (operator role) |
| GET  | `/auth/me` | Current user |
| POST | `/competencies` | Create a competency |
| GET  | `/competencies` | List competencies |
| GET  | `/competencies/{id}` | Get one (with full definition) |
| PUT  | `/competencies/{id}` | Update |
| DELETE | `/competencies/{id}` | Delete |
| POST | `/competencies/validate` | Validate a definition without storing |
| POST | `/competencies/{id}/execute` | Run a competency |
| GET  | `/competencies/{id}/performance` | Aggregate metrics |
| GET  | `/competencies/{id}/memory` | List memory entries |
| POST | `/competencies/{id}/memory` | Add a memory entry |
| DELETE | `/competencies/{id}/memory/{entry_id}` | Forget |
| GET  | `/competencies/{id}/audit-log` | Audit events for this competency |
| GET  | `/executions` | List executions |
| GET  | `/executions/{id}` | Get one |
| POST | `/executions/{id}/approve` | Approve / reject a pending execution |
| GET  | `/audit` | Cross-cutting audit query |

Full OpenAPI: open `http://localhost:8000/docs` after starting the API.

---

## RBAC

| Role | Permissions |
|---|---|
| `admin` | everything |
| `author` | competency.read/write/execute, memory.read/write, audit.read |
| `operator` | competency.read/execute, memory.read, audit.read |
| `viewer` | competency.read, memory.read, audit.read |

New users default to `operator`. Roles are stored in DB and seeded on first boot.

---

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `UCE_DATABASE_URL` | `sqlite:///./data/uce.db` | Postgres works too |
| `UCE_JWT_SECRET` | `dev-secret-change-me` | **change for prod** |
| `UCE_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT expiry |
| `UCE_LLM_PROVIDER` | `anthropic` | Default if competency.llm not set |
| `UCE_LLM_MODEL` | `claude-sonnet-4-6` | Default model |
| `UCE_CORS_ORIGINS` | `*` | Comma-separated |
| `UCE_BOOTSTRAP_ADMIN_EMAIL` | `admin@uce.local` | First boot only |
| `UCE_BOOTSTRAP_ADMIN_PASSWORD` | `changeme` | First boot only |
| `UCE_AUDIT_LOG_FILE` | _(unset)_ | Mirror events to a JSONL file |
| `ANTHROPIC_API_KEY` | _(required for Anthropic)_ | |
| `OPENAI_API_KEY` | _(required for OpenAI)_ | |

---

## Using UCE from other frameworks

UCE is provider-agnostic and **REST-first** — you can drive it from any agent framework.

- **LangChain / CrewAI / AutoGen** — call the REST API as a Tool. (Native python adapters are on the roadmap; the REST surface already makes this trivial.)
- **n8n / Zapier** — point an HTTP node at `POST /competencies/{id}/execute`.
- **Anthropic Claude / OpenAI / local LLMs** — set in `competency.llm.provider` and `competency.llm.model`. Switching is one-line.

---

## Roadmap (v0.2)

- Postgres production migrations via Alembic
- Visually polished Studio (drag-and-drop workflow designer)
- Plugin marketplace (sharing competencies)
- Native adapters for LangChain / CrewAI / AutoGen
- Vector memory plugin (Qdrant, Chroma, pgvector)
- Multi-tenant isolation
- Workflow live observability (server-sent events)

See `docs/IMPLEMENTATION_PLAN.md` for the build narrative and `docs/DESIGN.md` for architecture.

---

## License

MIT — see `LICENSE`. Author: Dr. Rami B. H.

---

## Acknowledgement

UCE is the production-real implementation of the *Competency vs Skill* framework
described in the accompanying study (`docs/COMPETENCY_VS_SKILL.md` — to be added).
The intent: shift from agents that *execute tasks* to competencies that
*understand missions, preserve context, follow policies, reason across domains,
learn from outcomes, and improve over time.*
