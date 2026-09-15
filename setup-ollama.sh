#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p .local/ollama
OLLAMA_VERSION="${OLLAMA_VERSION:-0.34.0}"

if [[ ! -x .local/ollama/bin/ollama ]]; then
  curl -fsSL --connect-timeout 15 --retry 3 \
    "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-amd64.tar.zst" \
    -o .local/ollama-linux-amd64.tar.zst
  tar --zstd -xf .local/ollama-linux-amd64.tar.zst -C .local/ollama
fi

export OLLAMA_MODELS="$PROJECT_DIR/.local/ollama/models"
export OLLAMA_HOST=127.0.0.1:11434
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if ! .venv/bin/python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)' >/dev/null 2>&1; then
  .local/ollama/bin/ollama serve > .local/ollama/server.log 2>&1 &
  server_pid=$!
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
    raise SystemExit("Ollama did not start. See .local/ollama/server.log")
PY
fi

model="$(.venv/bin/python -c 'from dotenv import dotenv_values; print(dotenv_values(".env").get("OLLAMA_MODEL", "llama3.2:3b"))')"
.local/ollama/bin/ollama pull "$model"
echo "Model installed. Run ./start.sh to start the app and Ollama."
