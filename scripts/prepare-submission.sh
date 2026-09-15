#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
.venv/bin/python scripts/package-submission.py
REVIEW_DIR="$(mktemp -d /tmp/lenny-source-review.XXXXXX)"
trap 'rm -rf "$REVIEW_DIR"' EXIT
.venv/bin/python - "$REVIEW_DIR" <<'PY'
import sys, zipfile
from pathlib import Path
target = Path(sys.argv[1])
with zipfile.ZipFile('submission/lenny-growth-assistant-source.zip') as archive:
    archive.extractall(target)
    for entry in archive.infolist():
        mode = entry.external_attr >> 16
        if mode:
            (target / entry.filename).chmod(mode & 0o777)
PY
SOURCE_DIR="$REVIEW_DIR/lenny-growth-assistant"
git init -q -b main "$SOURCE_DIR"
git -C "$SOURCE_DIR" add .
git -C "$SOURCE_DIR" -c user.name='Coding Agent' -c user.email='agent@localhost' commit -qm 'Prepare assignment source'
git -C "$SOURCE_DIR" bundle create "$PROJECT_DIR/submission/lenny-growth-assistant.bundle" --all
git -C "$SOURCE_DIR" bundle verify "$PROJECT_DIR/submission/lenny-growth-assistant.bundle"
git clone -q "$PROJECT_DIR/submission/lenny-growth-assistant.bundle" "$REVIEW_DIR/clone"
test -x "$REVIEW_DIR/clone/start.sh"
test ! -e "$REVIEW_DIR/clone/.env"
test ! -e "$REVIEW_DIR/clone/data"
.venv/bin/python - <<'PY'
import hashlib
from pathlib import Path
folder = Path('submission')
names = ['lenny-growth-assistant-source.zip', 'lenny-growth-assistant.bundle']
(folder / 'SHA256.txt').write_text(''.join(hashlib.sha256((folder / name).read_bytes()).hexdigest() + '  ' + name + '\n' for name in names))
PY
printf 'Reviewed archive and cloneable Git bundle are ready under submission/.\n'
