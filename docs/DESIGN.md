# Universal Competency Engine — Design (v0.1)

> Status: Approved 2026-05-17. Implements the 19-section spec provided by Dr. Rami B. H.

## 1. Purpose

UCE turns AI agents from **task executors** into **integrated expert competencies** that reason, remember, govern themselves, learn, and execute toward strategic objectives. A *Competency* is an integrated, reusable expert capability composed of skills + reasoning + workflows + memory + policies + objectives + governance + evaluation.

## 2. Non-goals

- Not a chatbot.
- Not a single agent framework.
- Not a workflow engine alone.
- Not a tool router alone.
- Not a UI for one specific LLM provider.

## 3. High-level architecture

```
                    ┌─────────────────────────┐
                    │  Studio (Next.js)       │
                    └──────────┬──────────────┘
                               │ REST/JSON (JWT)
                    ┌──────────▼──────────────┐
                    │   uce-api (FastAPI)     │  auth · routers · persistence
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   uce-runtime           │  reasoning · workflow · memory ·
                    │                         │  policy · executor · audit · eval
                    └────┬──────────┬─────────┘
                         │          │
                ┌────────▼──┐   ┌───▼──────────┐
                │ uce-llm   │   │  uce-core    │
                │ adapters  │   │  schema/sdk  │
                └───────────┘   └──────────────┘
```

## 4. Packages

| Package | Role |
|---|---|
| `uce-core` | Pydantic schema for Competency/Skill/Workflow/Policy/Memory/Objective/Agent. YAML loader, validator, common errors. Pure stdlib + pydantic. |
| `uce-runtime` | Reasoning planner, workflow orchestrator, memory store, policy engine, executor, audit logger, evaluator. |
| `uce-llm` | Provider-agnostic adapter: `LLMProvider` ABC + Anthropic/OpenAI/Ollama implementations. Plus a registry. |
| `uce-api` | FastAPI app with all spec'd endpoints, SQLAlchemy persistence, Alembic, JWT auth, RBAC. |
| `uce-cli` | `competency` CLI: create, validate, run, serve. |
| `apps/studio` | Next.js 15 + Tailwind + shadcn/ui UI. |
| `competencies/*` | Sample library (YAML competencies). |

## 5. Data model (relational)

`competencies, skills, workflows, policies, objectives, memory_entries, agents, executions, audit_logs, evaluations, users, roles, permissions, role_permissions, user_roles`.

Storage: SQLite by default (file `./data/uce.db`); Postgres via `UCE_DATABASE_URL`. `sqlite-vec` for embedding-backed semantic memory; pluggable to Qdrant/Chroma later.

## 6. Execution flow

`Request → CompetencyRouter → load(competency) → retrieve(memory) → policy.check(action,ctx) → reasoner.plan(objectives,policies,memory) → workflow.execute(plan) → validator.check(outputs) → governance.review(actions) → respond → memory.update(episode) → audit.log(span) → evaluator.score(run)`.

Each step is observable; every state transition produces an `audit_log` row with `run_id`, `span_id`, `actor`, `action`, `inputs`, `outputs`, `policy_decision`, `latency_ms`, `tokens_in`, `tokens_out`, `cost_estimate`.

## 7. Policy engine

`PolicyEngine.check(action, context) → Decision{Allow|Deny|RequireApproval, reasons, required_role?}`. Policies live in YAML alongside the competency, plus org-wide defaults. Decisions are written to `audit_logs` regardless of outcome.

## 8. Memory model

Six memory types (matches spec): `short_term, long_term, episodic, semantic, procedural, policy, decision, user_preference, organizational`. Backed by SQLite tables; semantic memory uses sqlite-vec for vector search. Retention/retrieval policies are per-memory-type.

## 9. Reasoning

`Reasoner.plan(goal, context) → Plan{steps[], confidence, risk, alignment_score, cost_estimate}`. Uses the LLM provider for free-form reasoning, but emits structured plans (Pydantic), so the executor can run them deterministically.

## 10. Workflow engine

YAML-defined steps: sequential, parallel, conditional, approval, escalation, fallback, retry, exception. Engine emits `executions` rows and supports resume from `pending_approval`.

## 11. Evaluation

Per-run metrics: success/failure, accuracy proxy (validator pass/fail), tokens, cost estimate, latency, policy violations, escalations. Aggregated per competency for dashboards.

## 12. Token optimization

- Memory reuse (retrieve before reason).
- Context compression (summary-of-summaries with size budget).
- Load only matching policies (tag-indexed).
- Cache reasoning plans (hash of goal+context → cached plan if confidence > threshold).
- Structured schemas instead of free-text round-trips.

## 13. Multi-LLM portability

`LLMProvider` ABC: `complete(messages, **opts) -> Response`, `stream(...)`, `embed(texts)`. Anthropic, OpenAI, Ollama implementations ship. Adding a new provider = ~80 LOC.

## 14. Security

- JWT auth (HS256; secret via env), refresh tokens.
- RBAC roles: `admin, author, operator, viewer`.
- Per-competency ACLs.
- All actions audit-logged.
- Sensitive fields redacted in logs via `SECRET_FIELDS` patterns.
- Policy check is required before any skill execution; bypass requires `admin` + emergency flag (audit-flagged).

## 15. Scope for v0.1 (this build)

| Component | v0.1 target |
|---|---|
| `uce-core`, `uce-runtime`, `uce-llm`, `uce-api`, `uce-cli` | Complete & real |
| `apps/studio` | Functional (auth, list/create/run, audit log viewer, perf dashboard) — minimal styling |
| Procurement sample | Fully built end-to-end |
| Legal, Cyber, HR samples | Schema stubs |
| Docker, README, CI | Complete |
| Postgres prod migrations, Studio polish, plugin marketplace, drag-drop workflow designer, native LangChain/CrewAI/AutoGen adapters | **Deferred to v0.2** (in roadmap) |

## 16. Out of scope / explicit deferrals

See above. UCE is usable from LangChain/CrewAI/AutoGen via REST out of the box; native adapters are convenience, not necessity.
