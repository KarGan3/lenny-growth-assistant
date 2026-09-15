#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
export APP_API_PORT="${APP_API_PORT:-8000}"
export APP_UI_PORT="${APP_UI_PORT:-5173}"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing Python environment: .venv/bin/python" >&2
  echo "Create .venv and install backend/requirements.txt first." >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to run the frontend." >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo "Install frontend dependencies first: cd frontend && npm install" >&2
  exit 1
fi
if [[ ! -d backend/pi-agent/node_modules/@mariozechner/pi-coding-agent ]]; then
  echo "Install the agent SDK first: cd backend/pi-agent && npm ci" >&2
  exit 1
fi

port_pair="$(.venv/bin/python - <<'PY'
import socket, os, sys
selected = []
for setting in ('APP_API_PORT', 'APP_UI_PORT'):
    requested = int(os.environ[setting])
    if not 1 <= requested <= 65535:
        raise SystemExit(f'{setting} must be between 1 and 65535.')
    for port in range(requested, 65536):
        if port in selected:
            continue
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(('127.0.0.1', port))
            except OSError:
                continue
        selected.append(port)
        if port != requested:
            print(f'Port {requested} is in use; using {port} for {setting}.', file=sys.stderr)
        break
    else:
        raise SystemExit(f'No free port found for {setting}.')
print(*selected)
PY
)"
read -r APP_API_PORT APP_UI_PORT <<< "$port_pair"

backend_pid=""
frontend_pid=""
ollama_pid=""
postgres_started=false
cleanup() {
  trap - EXIT INT TERM
  echo "Stopping frontend and backend..."
  [[ -z "$frontend_pid" ]] || kill "$frontend_pid" 2>/dev/null || true
  [[ -z "$backend_pid" ]] || kill "$backend_pid" 2>/dev/null || true
  [[ -z "$ollama_pid" ]] || kill "$ollama_pid" 2>/dev/null || true
  [[ -z "$frontend_pid" ]] || wait "$frontend_pid" 2>/dev/null || true
  [[ -z "$backend_pid" ]] || wait "$backend_pid" 2>/dev/null || true
  [[ -z "$ollama_pid" ]] || wait "$ollama_pid" 2>/dev/null || true
  if [[ "$postgres_started" == true ]]; then
    "$PROJECT_DIR/.local/postgres/usr/lib/postgresql/16/bin/pg_ctl" -D "$PROJECT_DIR/data/postgres" -m fast -w stop || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

mkdir -p data

database_driver="$(.venv/bin/python -c 'from dotenv import dotenv_values; import os; print(os.getenv("DATABASE_URL", dotenv_values(".env").get("DATABASE_URL", "sqlite")).split(":", 1)[0])')"
if [[ "$database_driver" == postgresql* && -f data/postgres/PG_VERSION ]]; then
  PG_ROOT="$PROJECT_DIR/.local/postgres"
  export LD_LIBRARY_PATH="$PG_ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  if ! "$PG_ROOT/usr/lib/postgresql/16/bin/pg_ctl" -D "$PROJECT_DIR/data/postgres" status >/dev/null 2>&1; then
    "$PG_ROOT/usr/lib/postgresql/16/bin/pg_ctl" -D "$PROJECT_DIR/data/postgres" -l "$PG_ROOT/server.log" \
      -o "-h 127.0.0.1 -p 5433 -k /tmp -c dynamic_library_path=$PG_ROOT/usr/lib/postgresql/16/lib" -w start
    postgres_started=true
  fi
fi

# Start the project-local model server if the configured local endpoint is down.
if [[ -x "$PROJECT_DIR/.local/ollama/bin/ollama" ]]; then
  export OLLAMA_MODELS="$PROJECT_DIR/.local/ollama/models"
  export OLLAMA_HOST=127.0.0.1:11434
  export OLLAMA_KEEP_ALIVE=30m
  export OLLAMA_CONTEXT_LENGTH="$(.venv/bin/python -c 'from dotenv import dotenv_values; import os; print(os.getenv("OLLAMA_CONTEXT_LENGTH", dotenv_values(".env").get("OLLAMA_CONTEXT_LENGTH", "8192")))')"
  if ! .venv/bin/python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)' >/dev/null 2>&1; then
    "$PROJECT_DIR/.local/ollama/bin/ollama" serve &
    ollama_pid=$!
    .venv/bin/python - <<'PY'
import time
import urllib.request
for _ in range(30):
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1)
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("Ollama did not start. Check its log above.")
PY
  fi
fi

echo "Loading the local model so the first question does not need to..."
.venv/bin/python - <<'PY'
import os
import httpx
from dotenv import dotenv_values
settings = {**dotenv_values('.env'), **os.environ}
if settings.get('LLM_PROVIDER', 'ollama').strip() == 'ollama':
    try:
        response = httpx.post(settings.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/') + '/api/generate',
                              json={'model': settings.get('OLLAMA_MODEL', 'llama3.2:3b'), 'keep_alive': '30m'}, timeout=30)
        response.raise_for_status()
        print('Local model ready.')
    except Exception:
        print('Model warmup did not complete; check Ollama if generation fails.')
PY

.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port "$APP_API_PORT" &
backend_pid=$!

# Wait for FastAPI before opening Vite, preventing failed initial UI requests.
.venv/bin/python - <<'PY'
import time
import urllib.request
import os
for _ in range(30):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{os.environ["APP_API_PORT"]}/health', timeout=2)
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit('Backend did not become ready. Check its log above.')
PY

kill -0 "$backend_pid" 2>/dev/null || { echo 'Backend exited during startup.' >&2; exit 1; }

# Run Vite directly so cleanup targets the actual server process.
export VITE_PROXY_TARGET="http://127.0.0.1:$APP_API_PORT"
(
  cd "$PROJECT_DIR/frontend"
  exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$APP_UI_PORT" --strictPort
) &
frontend_pid=$!

echo "Frontend: http://127.0.0.1:$APP_UI_PORT/"
echo "Backend:  http://127.0.0.1:$APP_API_PORT/docs"
echo "Press Ctrl+C to stop servers started by this script."

# If either server exits, stop the other and preserve the exit status.
status=0
wait -n "$backend_pid" "$frontend_pid" || status=$?
exit "$status"
