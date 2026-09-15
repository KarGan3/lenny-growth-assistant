"""Install pinned public CPU entailment weights with checksum/atomic-write verification."""
import hashlib
from pathlib import Path
import sys
import httpx

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
from app.config import Settings

revision = 'fa2804872c3b4bd748f38c0185cc85775361e735'
files = {
    'model.onnx': ('onnx/model_quint8_avx2.onnx', '03c2221313dc0c3eac9cec1f746d1319d33f2c2901fcce1c0f08f4daac9b6dae'),
    'tokenizer.json': ('tokenizer.json', '5124ef2ead1a10a717703bc436de7f353da76d6340e4587719b42b1693707964'),
    'config.json': ('config.json', '885d0dceae8fa5c136da9209121ec9eb11160488e840de3bc1f29353674e5712'),
}
folder = Path(Settings().EVIDENCE_MODEL_DIR)
folder.mkdir(parents=True, exist_ok=True)
with httpx.Client(follow_redirects=True, timeout=180) as client:
    for name, (remote, checksum) in files.items():
        target = folder / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == checksum:
            continue
        temporary = target.with_suffix(target.suffix + '.download')
        try:
            with client.stream('GET', f'https://huggingface.co/cross-encoder/nli-deberta-v3-small/resolve/{revision}/{remote}') as response:
                response.raise_for_status()
                with temporary.open('wb') as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != checksum:
                raise RuntimeError(f'Checksum mismatch for {name}')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f'Installed verified {name}', flush=True)
print('Local source verifier is installed.')
