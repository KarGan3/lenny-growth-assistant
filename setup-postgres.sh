#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
PG_ROOT="$PROJECT_DIR/.local/postgres"
PG_BIN="$PG_ROOT/usr/lib/postgresql/16/bin"
export LD_LIBRARY_PATH="$PG_ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$PG_ROOT/packages"
if [[ ! -x "$PG_BIN/postgres" ]]; then
  (cd "$PG_ROOT/packages" && apt-get download postgresql-16 postgresql-client-16 libpq5)
  for package in "$PG_ROOT"/packages/*.deb; do
    dpkg-deb -x "$package" "$PG_ROOT"
  done
fi
if [[ ! -f data/postgres/PG_VERSION ]]; then
  "$PG_BIN/initdb" -D "$PROJECT_DIR/data/postgres" -L "$PG_ROOT/usr/share/postgresql/16" \
    --username=lenny --auth=trust --encoding=UTF8
fi
if ! "$PG_BIN/pg_ctl" -D "$PROJECT_DIR/data/postgres" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$PROJECT_DIR/data/postgres" -l "$PG_ROOT/server.log" \
    -o "-h 127.0.0.1 -p 5433 -k /tmp -c dynamic_library_path=$PG_ROOT/usr/lib/postgresql/16/lib" -w start
fi
.venv/bin/python - <<'PY'
import psycopg
with psycopg.connect('host=127.0.0.1 port=5433 user=lenny dbname=postgres', autocommit=True) as db:
    if not db.execute("SELECT 1 FROM pg_database WHERE datname = 'lenny_growth_assistant'").fetchone():
        db.execute('CREATE DATABASE lenny_growth_assistant')
print('PostgreSQL ready: postgresql+psycopg://lenny@127.0.0.1:5433/lenny_growth_assistant')
PY
