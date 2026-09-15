#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
for required in python3 npm git curl zstd dpkg-deb; do
  command -v "$required" >/dev/null || { echo "Install $required first (see README.md)." >&2; exit 1; }
done
[[ -x .venv/bin/python ]] || python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-lock.txt
(cd frontend && npm ci)
(cd backend/pi-agent && npm ci)
[[ -f .env ]] || cp .env.example .env
[[ -f frontend/.env ]] || cp frontend/.env.example frontend/.env
.venv/bin/python scripts/setup-evidence.py
./setup-postgres.sh
./setup-ollama.sh
[[ -f data/chroma/corpus-manifest.json ]] || ./scripts/refresh-knowledge.sh
printf 'Setup complete. Run ./start.sh and open http://127.0.0.1:5173/\n'
