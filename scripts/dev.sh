#!/usr/bin/env bash
# Start API + Studio in dev mode.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

(cd "$ROOT" && uv run uvicorn uce_api.main:app --reload --host 0.0.0.0 --port 8000) &
API_PID=$!

(cd "$ROOT/apps/studio" && npm run dev) &
STUDIO_PID=$!

trap 'kill $API_PID $STUDIO_PID 2>/dev/null || true' EXIT
wait
