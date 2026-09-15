#!/usr/bin/env bash
# Build separately, then swap only a completed index. Stop the app before refreshing.
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
if curl -fsS --max-time 2 "http://127.0.0.1:${APP_API_PORT:-8000}/health" >/dev/null 2>&1; then
  echo 'Stop the app before refreshing knowledge.' >&2; exit 1
fi
SOURCE_REVISION="${TRANSCRIPT_REVISION:-be8ab89a890a833cbba2c892178f823fff178c65}"
if [[ ! -d rag/data_repo/.git ]]; then
  git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git rag/data_repo
fi
git -C rag/data_repo fetch origin
git -C rag/data_repo checkout --detach "$SOURCE_REVISION"
.venv/bin/python -u scripts/rebuild-knowledge.py --repo rag/data_repo
