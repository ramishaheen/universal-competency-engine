#!/usr/bin/env bash
# Walk through the UCE API with curl. Requires the API running at :8000.
set -euo pipefail

API=${API:-http://localhost:8000}
EMAIL=${EMAIL:-admin@example.com}
PASSWORD=${PASSWORD:-changeme}

echo "→ login"
TOKEN=$(curl -sS -X POST "$API/auth/login" \
  -d "username=$EMAIL&password=$PASSWORD" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"

echo "→ create competency from YAML"
PAYLOAD=$(python3 -c "
import json, yaml, sys
with open('competencies/procurement/competency.yaml') as f:
    d = yaml.safe_load(f)
print(json.dumps({'definition': d}))
")
curl -sS -X POST "$API/competencies" -H "$AUTH" -H "Content-Type: application/json" -d "$PAYLOAD" | head -c 500
echo

echo "→ execute it"
curl -sS -X POST "$API/competencies/procurement/execute" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"inputs": {"request": "Buy 25 monitors", "budget_usd": 12000}, "run_plan": false}' \
  | head -c 2000
echo

echo "→ list executions"
curl -sS "$API/executions" -H "$AUTH" | head -c 1500
echo
