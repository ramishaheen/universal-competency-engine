# Procurement Competency (sample)

Full reference competency. Demonstrates every layer: skills, workflow with
parallel/conditional/approval branches, policies (allow / require_approval /
deny), memory, evaluation, agents.

Run it:

```bash
competency validate competencies/procurement/competency.yaml
competency run competencies/procurement/competency.yaml \
  --inputs '{"request": "Buy 50 laptops for the engineering team", "budget_usd": 75000, "deadline": "2026-06-30"}'
```

If `budget_usd > 50000`, the workflow halts at the `approve_high_value` step
with `status=pending_approval` — approve it via the API:

```bash
curl -X POST http://localhost:8000/executions/<id>/approve \
  -H "Authorization: Bearer <token>" \
  -d '{"approved": true, "note": "approved for engineering refresh"}'
```
