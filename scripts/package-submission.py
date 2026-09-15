"""Create an evaluator source archive from a strict allowlist, never from .env/local data."""
from pathlib import Path
import zipfile
import re
import hashlib
import os

root=Path(__file__).resolve().parents[1]
top_files={'README.md','PRD.md','design.md','architecture.md','.env.example','.gitignore',
           'start.sh','setup.sh','setup-ollama.sh','setup-postgres.sh'}
folders={'backend','frontend','rag','docs','agent-transcripts','scripts'}
blocked={'node_modules','__pycache__','.pytest_cache','dist','.git','data','data_repo','.local','.venv','test-results','playwright-report'}
files=[]
candidate_files=[]
for directory, subdirs, names in os.walk(root):
    current=Path(directory)
    subdirs[:] = sorted(name for name in subdirs if name not in blocked and
                        (current != root or name in folders) and not (current/name).is_symlink())
    candidate_files.extend(current/name for name in names)
for path in sorted(candidate_files):
    if path.is_symlink(): continue
    if not path.is_file(): continue
    rel=path.relative_to(root)
    if any(part in blocked for part in rel.parts): continue
    if rel.name == '.env' or rel.suffix in {'.db','.log','.pyc','.tmp'}: continue
    if len(rel.parts)==1 and rel.name not in top_files: continue
    if len(rel.parts)>1 and rel.parts[0] not in folders: continue
    data=path.read_bytes()
    if re.search(rb'(?:sk-ant-api\d{2}-[A-Za-z0-9_-]{25,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',data):
        raise SystemExit(f'Possible credential in {rel}; archive not created.')
    files.append(path)
output=root/'submission';output.mkdir(exist_ok=True)
archive=output/'lenny-growth-assistant-source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in files:
        z.write(path, 'lenny-growth-assistant/'+str(path.relative_to(root)))
(output/'SHA256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(f'Packaged {len(files)} reviewed source files: {archive}')
