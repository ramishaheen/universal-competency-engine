# UCE REST API

The full, live OpenAPI spec is served at `http://localhost:8000/openapi.json` and the interactive UI at `http://localhost:8000/docs`. This file is a short cheat-sheet.

## Authentication

JWT bearer. Get one via `POST /auth/login` (form fields `username` + `password`).

```bash
curl -X POST http://localhost:8000/auth/login \
  -d 'username=admin@example.com&password=changeme'
```

## Endpoints

| Verb | Path | Permission |
|---|---|---|
| GET  | `/health` | — |
| POST | `/auth/login` | — |
| POST | `/auth/register` | — |
| GET  | `/auth/me` | authenticated |
| POST | `/competencies` | `competency.write` |
| GET  | `/competencies` | `competency.read` |
| GET  | `/competencies/{id}` | `competency.read` |
| PUT  | `/competencies/{id}` | `competency.write` |
| DELETE | `/competencies/{id}` | `competency.write` |
| POST | `/competencies/validate` | authenticated |
| POST | `/competencies/{id}/execute` | `competency.execute` |
| GET  | `/competencies/{id}/performance` | `audit.read` |
| GET  | `/competencies/{id}/memory` | `memory.read` |
| POST | `/competencies/{id}/memory` | `memory.write` |
| DELETE | `/competencies/{id}/memory/{entry_id}` | `memory.write` |
| GET  | `/competencies/{id}/audit-log` | `audit.read` |
| GET  | `/executions` | `competency.read` |
| GET  | `/executions/{id}` | `competency.read` |
| POST | `/executions/{id}/approve` | `competency.approve` |
| GET  | `/audit` | `audit.read` |

## Execution lifecycle

```
POST /competencies/{id}/execute
   ├─ status: succeeded         → outputs ready
   ├─ status: failed            → error filled
   ├─ status: denied            → policy denied
   └─ status: pending_approval  → human action needed
                                ↓
                  POST /executions/{exec_id}/approve  →  resumed run
```

When an execution is `pending_approval`, the original `ExecutionRow` is frozen
and the approval endpoint creates a **new** execution that continues from the
top with elevated actor roles.
