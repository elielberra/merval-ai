#!/usr/bin/env bash
# Start the merval-ai backend (API) and frontend together for local development.
# Usage: ./start.sh    (Ctrl+C stops both)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# --- One-time setup if needed ---
if [ ! -d "$BACKEND/.venv" ]; then
  echo "Creating backend virtualenv and installing dependencies..."
  python3 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
fi

if [ ! -f "$BACKEND/.env" ]; then
  echo "WARNING: $BACKEND/.env not found. Copy backend/.env.example to backend/.env"
  echo "         and add your ANTHROPIC_API_KEY (needed to run the research analysis)."
fi

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install)
fi

# --- Start both, and stop both together ---
pids=()
cleanup() {
  echo
  echo "Stopping backend and frontend..."
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Starting backend  -> http://localhost:$BACKEND_PORT"
( cd "$BACKEND" && exec .venv/bin/uvicorn api:app --port "$BACKEND_PORT" ) &
pids+=($!)

echo "Starting frontend -> http://localhost:$FRONTEND_PORT"
( cd "$FRONTEND" && exec npm run dev -- --port "$FRONTEND_PORT" ) &
pids+=($!)

echo
echo "Both running. Open http://localhost:$FRONTEND_PORT  (Ctrl+C to stop both)."
wait
