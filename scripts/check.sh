#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
PYTHONPATH=backend RAG_PERSIST_DIR=./data/chroma RAG_EMBEDDER=local-lexical .venv/bin/python -m pytest backend/tests -q
PYTHONPATH=rag .venv/bin/python -m pytest rag/tests -q
(cd frontend && npm test && npm run build)
bash -n start.sh setup.sh setup-ollama.sh setup-postgres.sh scripts/refresh-knowledge.sh scripts/prepare-submission.sh
.venv/bin/python -m compileall -q backend/app rag scripts
