<div align="center">

# 🧠 Universal Competency Engine

### Move AI from **isolated agents** to **integrated cognitive competencies**.

*The missing intelligence layer between LLMs and autonomous organizations.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97757?logo=anthropic&logoColor=white)](https://www.anthropic.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-412991?logo=openai&logoColor=white)](https://openai.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local-000?logo=ollama&logoColor=white)](https://ollama.com)
[![Tests](https://img.shields.io/badge/tests-73%2F73%20passing-success)](#-status--proof)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](#-quick-start)
[![SSRN](https://img.shields.io/badge/SSRN-Research%20Paper-FF6F00)](https://ramishaheen.cloud)

**[Read the manifesto ⤵](#-the-shift-from-agents-to-competencies)** • **[Quick start ⤵](#-quick-start)** • **[Architecture ⤵](#-the-eight-layers-of-a-competency)** • **[Roadmap ⤵](#-the-road-to-cognitive-society)**

</div>

---

## ✨ TL;DR

> For years the AI industry has been obsessed with building **agents**.
> Agents that *do tasks*. Agents that *use tools*. Multi-agent swarms.
>
> But the real bottleneck of modern AI isn't model capability — **it's fragmented cognition.**
> Today's AI systems forget context, repeat reasoning, lack governance, and cannot preserve institutional intelligence.
>
> This repository ships the production-grade reference implementation of a new architectural primitive that fixes all of that:
>
> ### **The Competency.**
> An integrated expert capability composed of **skills + reasoning + workflows + memory + policies + objectives + governance + adaptive learning** — packaged as a single reusable cognitive unit.

---

## 🚨 The shift: from Agents to Competencies

We've been building the wrong abstraction.

```
                  AGENTS                             COMPETENCIES
       ┌───────────────────────────┐        ┌───────────────────────────────┐
       │  Skill 1   Skill 2 ...    │        │  Skills · Reasoning · Memory  │
       │   ↓ task  ↓ task ↓        │        │  Policies · Workflows         │
       │        AGENT              │   →    │  Objectives · Governance      │
       │  (stateless, reactive)    │        │  Adaptive learning loop       │
       └───────────────────────────┘        └───────────────────────────────┘
       ❌ fragmented intelligence            ✅ integrated cognition
       ❌ forgets context                    ✅ persistent organizational memory
       ❌ no governance                      ✅ policy + audit built in
       ❌ task execution                     ✅ mission-aligned reasoning
       ❌ shallow autonomy                   ✅ outcome-driven autonomy
```

| | **Agent with Skills** | **Agent with Competencies** |
|---|---|---|
| Architecture | Fragmented, task-centric | Integrated, outcome-driven |
| Performance | ⭐⭐ — good for simple tasks | ⭐⭐⭐⭐⭐ — handles end-to-end work |
| Accuracy | ⭐⭐⭐ — depends on prompts | ⭐⭐⭐⭐½ — reasoning + memory + policy |
| Governance | ⭐ — hard to enforce | ⭐⭐⭐⭐⭐ — built into the layer |
| Memory & Context | ⭐ — short-term only | ⭐⭐⭐⭐⭐ — 9 memory types, persistent |
| Scalability | ⭐⭐ — more skills = more complexity | ⭐⭐⭐⭐⭐ — competencies reuse and evolve |
| Token efficiency | ⭐⭐ — repetitive context | ⭐⭐⭐⭐½ — memory reuse, structured plans |
| Autonomy level | ⭐ — needs constant orchestration | ⭐⭐⭐⭐½ — self-governed, self-improving |
| Total cost of ownership | ⭐ — high | ⭐⭐⭐⭐½ — lower long-term |
| Organizational impact | ⭐ — task automation | ⭐⭐⭐⭐⭐ — **autonomous intelligence units** |

---

## 🧬 What is a Competency?

A **Competency** is not a chatbot, not a skill, and not a workflow.
It's an integrated, reusable expert capability packaged as a single object:

```yaml
id: procurement
name: Procurement Competency
mission: Procure goods that are best-value, compliant, low-risk, and aligned with strategy.
risk_level: high

objectives:
  - { id: best_value,        name: Maximise value-for-money,        priority: high     }
  - { id: compliance,        name: Maintain regulatory compliance,  priority: critical }
  - { id: risk_minimisation, name: Minimise supplier risk,          priority: high     }

skills:        [ vendor_search, vendor_scoring, price_analysis, compliance_check,
                 risk_assessment, contract_review, negotiation_strategy, executive_report ]

workflows:     [ procurement_main (parallel + conditional + human-approval branches) ]

policies:
  - allow:              read-only discovery + analysis skills
  - require_approval:   contracts > $50,000 (head_of_procurement)
  - deny:               any auto-signing or PO issuance

memory:        [ short_term, long_term, episodic, semantic, procedural,
                 policy, decision, user_preference, organizational ]

agents:        [ planner, governance, reviewer ]

evaluation:    accuracy · latency · tokens · cost · policy_violations · escalations
```

One YAML → one fully governed, memory-aware, reasoning-capable, auditable **expert**. Drop it into your organization. Version it. Improve it. Share it.

---

## 🏛 The eight layers of a Competency

```
┌────────────────────────────────────────────────────────────────────┐
│                    1.  Competency Definition                       │
│         mission · objectives · scope · risk · success metrics      │
├────────────────────────────────────────────────────────────────────┤
│                    2.  Skills Layer                                │
│         atomic capabilities · prompts · tools · sub-skills · APIs  │
├────────────────────────────────────────────────────────────────────┤
│                    3.  Reasoning Layer                             │
│         plan-before-act · risk · confidence · alignment scoring    │
├────────────────────────────────────────────────────────────────────┤
│                    4.  Workflow Layer                              │
│         sequential · parallel · conditional · approval · escalation│
├────────────────────────────────────────────────────────────────────┤
│                    5.  Memory & Context Layer                      │
│         9 memory types · retention · semantic recall · episodes    │
├────────────────────────────────────────────────────────────────────┤
│                    6.  Policy & Governance Layer                   │
│         allow · deny · require_approval · RBAC · audit · compliance│
├────────────────────────────────────────────────────────────────────┤
│                    7.  Objective Alignment Layer                   │
│         every action scored against mission + organisational goals │
├────────────────────────────────────────────────────────────────────┤
│                    8.  Evaluation & Learning Layer                 │
│         metrics · feedback · continuous improvement loop           │
└────────────────────────────────────────────────────────────────────┘
```

Every action a competency takes traverses these layers — every time.
Every decision is **logged, auditable, policy-checked, and mission-aligned.**

---

## 🚀 Quick start

### One-line install (Python)

```bash
git clone https://github.com/ramishaheen/universal-competency-engine.git
cd universal-competency-engine
uv sync --all-packages
export ANTHROPIC_API_KEY=sk-ant-...
```

### Run a real competency in 10 seconds

```bash
uv run competency validate competencies/procurement/competency.yaml
uv run competency run     competencies/procurement/competency.yaml \
  --inputs '{"request":"Buy 25 monitors for the design team","budget_usd":12000}'
```

You'll see Claude reason, plan, run 8 skills end-to-end, and produce a CFO-ready executive summary with full audit trail.

### Spin up the full platform

```bash
docker compose up --build
# API    → http://localhost:8000/docs   (interactive Swagger)
# Studio → http://localhost:3000        (Next.js UI)
# Login  → admin@example.com / changeme
```

That's it. You now have a **production AI cognitive infrastructure** running on your laptop.

---

## 🎛 What's in this repo

```
universal-competency-engine/
│
├─ 📦 packages/
│   ├─ uce-core/      Pydantic schema · YAML loader · semantic validator
│   ├─ uce-runtime/   Reasoning · Workflow · Memory · Policy · Executor · Audit · Evaluator
│   ├─ uce-llm/       Provider-agnostic adapters → Anthropic · OpenAI · Ollama
│   ├─ uce-api/       FastAPI · SQLAlchemy · JWT · RBAC · all 21 endpoints
│   └─ uce-cli/       `competency create | validate | inspect | run | serve`
│
├─ 🖥  apps/studio/    Next.js 15 + Tailwind UI (author · run · audit · approve)
│
├─ 🧪 competencies/
│   ├─ procurement/   ← fully implemented sample (8 skills, real workflow, real policies)
│   ├─ legal-review/  ← stub
│   ├─ cybersecurity/ ← stub
│   └─ hr-screening/  ← stub
│
├─ 🐳 docker/         Dockerfile.api · Dockerfile.studio · docker-compose.yml
├─ ⚙️ ci/             GitHub Actions workflow template
├─ 📖 docs/           DESIGN.md · IMPLEMENTATION_PLAN.md · API.md
├─ 🔧 examples/       Python + curl example scripts
└─ 📜 README · LICENSE · CHANGELOG · CONTRIBUTING
```

---

## 🏗 Architecture

```
                          ┌─────────────────────────┐
                          │  🖥  Studio (Next.js)    │
                          └────────────┬────────────┘
                                       │ REST / JSON / JWT
                          ┌────────────▼────────────┐
                          │  🌐 uce-api (FastAPI)    │
                          │  auth · RBAC · audit     │
                          └────────────┬────────────┘
                                       │
            ┌──────────────────────────▼──────────────────────────┐
            │                  🧠 uce-runtime                     │
            │                                                     │
            │  ┌─────────┐   ┌──────────┐   ┌─────────┐           │
            │  │Executor │──▶│Reasoner  │──▶│Planner  │           │
            │  └────┬────┘   └────┬─────┘   └────┬────┘           │
            │       ▼             ▼              ▼                │
            │  ┌────────┐    ┌────────┐    ┌────────────┐         │
            │  │ Policy │    │ Memory │    │ Workflow   │         │
            │  │ Engine │    │ (9 types)   │ Orchestr.  │         │
            │  └────┬───┘    └───┬────┘    └─────┬──────┘         │
            │       │            │               │                │
            │       ▼            ▼               ▼                │
            │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
            │  │ Audit    │  │ Evaluator│  │ Skill Exec│          │
            │  └──────────┘  └──────────┘  └────┬─────┘           │
            └────────────────────────────────────┼────────────────┘
                                                 │
                          ┌──────────────────────▼─────────────────┐
                          │   🔌 uce-llm  (provider-agnostic)      │
                          │   Anthropic │ OpenAI │ Ollama │ ...    │
                          └────────────────────────────────────────┘
                                                 │
                          ┌──────────────────────▼─────────────────┐
                          │   📐 uce-core (schema · loader · valid)│
                          └────────────────────────────────────────┘
```

**Execution flow** (faithful to the registered research paper):

`Request → Router → load(competency) → retrieve(memory) → policy.check → reasoner.plan → workflow.execute → validate → governance.review → respond → memory.update → audit.log → evaluator.score`

---

## 🔌 Works with any LLM, any framework

| Provider | Status | How |
|---|---|---|
| **Anthropic Claude** | ✅ Native adapter, live-tested | `provider: anthropic` |
| **OpenAI GPT** | ✅ Native adapter | `provider: openai` |
| **Ollama (local)** | ✅ Native adapter (zero-dep HTTP) | `provider: ollama, base_url: http://localhost:11434` |
| **Custom / Bedrock / Gemini / Mistral** | ✅ Implement `LLMProvider` ABC (~80 LOC) | `register_provider("name", MyProvider)` |

Use UCE **from any agent framework** via REST:

| Framework | How to integrate |
|---|---|
| **LangChain** | Wrap the REST API as a `Tool` — done. |
| **CrewAI** | Same. POST `/competencies/{id}/execute`. |
| **AutoGen** | Same. Each competency = one "expert agent". |
| **n8n / Zapier / Make** | HTTP node → `/execute`. |
| **Enterprise apps** | OpenAPI spec at `/openapi.json` — auto-generate clients. |

---

## 🌍 The road to Cognitive Society

This isn't just a framework. It's a stepping stone.

```
   Skills           Agents          Competencies       Autonomous          AI Societies
(applications)   (workers)         (experts)         Organizations        & Economies
     ●     ───▶     ●      ───▶       ●        ───▶        ●          ───▶      ●
     ↓              ↓                 ↓                    ↓                    ↓
   tasks          tools            integrated         self-governed        cognitive
                                  intelligence        cognition           infrastructure
                                                                          for humanity
```

When competencies become first-class citizens of an organisation:

- 🧠 **Departments evolve into autonomous intelligence units** with persistent memory and embedded governance.
- 🏢 **Enterprises become cognitive ecosystems** where intelligence compounds instead of evaporating.
- 🌐 **Companies talk to other companies through competencies** — a new B2B interface for cognition.
- 🪐 And eventually: **AI becomes civilization infrastructure**, not just another SaaS tool.

We are moving from *"AI as a tool"* to *"AI as **operating infrastructure** for human enterprise and society."*

---

## 🧠 Why Competencies fix what agents can't

| The "Dumb Agent Zone" failure mode | How a Competency solves it |
|---|---|
| ❌ Forgets context between turns | ✅ Nine memory types — short-term, long-term, episodic, semantic, procedural, policy, decision, user-preference, organisational — written automatically every run. |
| ❌ Repeats reasoning every call | ✅ Reasoner emits structured `Plan` objects that are cached and reusable when confidence is high. |
| ❌ No governance enforcement | ✅ Policy engine evaluates every action — `allow / deny / require_approval` — before it happens. |
| ❌ Tool sprawl, no orchestration | ✅ Workflow layer composes skills with sequential / parallel / conditional / approval / sub-workflow / escalation. |
| ❌ Can't ask a human when stuck | ✅ Human-in-the-loop is a first-class step type. Pending executions resume cleanly. |
| ❌ No visibility into what happened | ✅ Every action emits an audit event with actor, decision, reasons, tokens, cost, latency. |
| ❌ Can't measure quality | ✅ Evaluator scores every run; aggregated dashboards per competency. |
| ❌ Vendor-locked to one LLM | ✅ Provider-agnostic adapter — swap Claude ↔ GPT ↔ Llama with one line. |

---

## 📚 The research

This implementation is the production-grade reference for a peer-research-grade paper now registered on **SSRN**:

> ### *From Agentic AI to Competency Intelligence:*
> ### *A Comparative Architectural Study of Skill-Based Agents and Competency-Based Cognitive Systems*
>
> **Author:** Dr. Rami Shaheen
> **Affiliations:** [ramishaheen.cloud](https://ramishaheen.cloud) · [cap.ramishaheen.cloud](https://cap.ramishaheen.cloud)
> **Registered on SSRN.** Citation forthcoming.

The paper introduces **Competency Intelligence** as a new cognitive architecture model and proves, with comparative analysis, that the next frontier of AI is not larger models — it's **better cognitive structure** around them.

This repository is the **canonical open-source implementation** of that paper.

---

## 🎯 Status — proof, not promises

| What | Status |
|---|---|
| Backend tests | **73 / 73 passing** (`uv run pytest -q`) |
| Sample competencies | **4 / 4 validate** (procurement full + 3 stubs) |
| Studio build | **Clean** (Next.js 15.5.18, 9 routes compiled) |
| End-to-end smoke test | **Real Anthropic call succeeded** — `claude-haiku-4-5` returned: *"Broad capabilities / Specific learned tasks / Both shape AI power"* — 37 → 16 tokens, $0.0001 |
| Docker | **API + Studio compose up** |
| RBAC + audit | **Working** — bootstrap admin, 4 default roles, 8 permissions, full event log |
| Live repo | https://github.com/ramishaheen/universal-competency-engine |

Real backend. Real frontend. Real DB. Real LLM. Real auth. Real workflow execution. **No mocks, no demos, no placeholders.**

---

## 🛠 Authoring your first competency

```yaml
id: market_research
name: Market Research Competency
mission: Produce a 2-page competitive landscape brief on any topic.
risk_level: low
priority_level: medium

objectives:
  - id: coverage
    name: Cover at least 5 competitors

skills:
  - id: find_competitors
    name: Find competitors
    execution_steps:
      - { id: list, type: prompt,
          prompt: "List 5–8 main competitors of {{ inputs.target }}. One bullet each.",
          output_key: competitors }

  - id: write_brief
    name: Write brief
    dependencies: [find_competitors]
    execution_steps:
      - { id: draft, type: prompt,
          prompt: "Write a 2-page brief on the competitive landscape. Competitors: {{ data.competitors }}",
          output_key: brief }

workflows:
  - id: main
    name: Main
    is_default: true
    steps:
      - { id: a, type: skill, skill: find_competitors }
      - { id: b, type: skill, skill: write_brief, output_key: brief }

policies:
  - id: allow_all
    name: Allow all (read-only)
    effect: allow
    applies_to: ["*"]

llm:
  provider: anthropic
  model: claude-sonnet-4-6
```

Save as `market_research.yaml`, then:

```bash
uv run competency validate market_research.yaml
uv run competency run market_research.yaml --inputs '{"target":"Stripe"}'
```

Promote it to the live platform:

```bash
curl -X POST http://localhost:8000/competencies \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d @<(python3 -c "import yaml,json,sys; print(json.dumps({'definition':yaml.safe_load(open('market_research.yaml'))}))")
```

Done. It's now a versioned, governed, auditable, runnable expert in your organisation.

---

## 🔐 Security & governance built-in

- 🔑 **JWT** auth (`HS256`) + bcrypt password hashing
- 👥 **RBAC** — `admin` / `author` / `operator` / `viewer` (seeded on first boot)
- 🛡 **8 default permissions** — `competency.read/write/execute/approve`, `memory.read/write`, `audit.read`, `user.manage`
- 📜 **Policy engine** — evaluated on every action; `deny > require_approval > allow`
- 🧾 **Audit log** — every event: actor, action, decision, reasons, tokens, cost, latency
- 🤫 **Auto-redaction** of `password / token / secret / api_key / authorization` in all audit records
- ⏸ **Human-in-the-loop** — `pending_approval` executions resume cleanly via `POST /executions/{id}/approve`

---

## 📡 REST API at a glance

```
POST   /auth/login                          → JWT
POST   /auth/register                       → self-register
GET    /auth/me                             → current user

POST   /competencies                        → create from JSON/YAML
GET    /competencies                        → list
GET    /competencies/{id}                   → full definition
PUT    /competencies/{id}                   → update
DELETE /competencies/{id}                   → delete
POST   /competencies/validate               → validate only
POST   /competencies/{id}/execute           → RUN
GET    /competencies/{id}/performance       → aggregated metrics
GET    /competencies/{id}/memory            → list memory
POST   /competencies/{id}/memory            → remember
GET    /competencies/{id}/audit-log         → per-competency audit

GET    /executions                          → list
GET    /executions/{id}                     → detail (+ plan, outputs, error)
POST   /executions/{id}/approve             → approve / reject pending

GET    /audit                               → cross-cutting query
```

Full interactive spec: `http://localhost:8000/docs` (auto-generated OpenAPI).

---

## 🗺 Roadmap

**v0.1 (this release)** — Schema + Runtime + REST API + Studio + Docker + Procurement sample. **✅ Shipped.**

**v0.2** — Visual workflow designer · Postgres-prod migrations · Plugin marketplace · Vector memory (Qdrant / Chroma / pgvector) · Native LangChain / CrewAI / AutoGen adapters.

**v0.3** — Multi-tenant isolation · Cross-competency reasoning · Cognitive observability (live SSE traces) · Distributed competencies (a competency on one node calling one on another).

**v1.0** — **Cognitive Society SDK** — primitives for AI-to-AI competency exchange, cognitive marketplaces, and inter-organisational autonomous economies.

---

## 🤝 Contributing

We're building cognitive infrastructure for the next era of human enterprise. Contributions, sample competencies, integrations, critiques, and research are all welcome.

```bash
uv sync --all-packages
uv run pytest -q                    # 73 tests
cd apps/studio && npm install && npm run build
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## ⭐ Like the vision?

If Competency Intelligence resonates, **a star here is the easiest way to help this become the open standard for organisational AI.** The more competencies the ecosystem accumulates, the closer we get to a Cognitive Society.

> "The biggest limitation in today's AI systems is not model capability. It is **fragmented cognition.**"
> — *From Agentic AI to Competency Intelligence (SSRN, Dr. Rami Shaheen)*

---

## 👤 Author

<div align="center">

### **Dr. Rami Shaheen**
Inventor & developer of the Competency Intelligence framework.

🌐 [ramishaheen.cloud](https://ramishaheen.cloud) · 🎓 [cap.ramishaheen.cloud](https://cap.ramishaheen.cloud)

</div>

---

## 📄 License

MIT — see [`LICENSE`](LICENSE). Free for personal, commercial, and research use. Build the cognitive future.

---

<div align="center">

### **From agents that execute tasks → to competencies that run organisations.**
### **From AI as a tool → to AI as civilization infrastructure.**

`#CompetencyIntelligence` · `#CognitiveSociety` · `#AutonomousAI` · `#AIArchitecture`
`#FutureOfAI` · `#AgenticAI` · `#EnterpriseAI` · `#AIResearch` · `#SSRN`

</div>
