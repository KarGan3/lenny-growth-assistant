#!/usr/bin/env python3
"""Rebuild the entire local transcript index and refuse incomplete coverage."""
import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rag'))
from ingest import parse_transcript, chunk_episode, split_long_turns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT / 'rag/data_repo')
    parser.add_argument('--target-tokens', type=int, default=350)
    parser.add_argument('--overlap-turns', type=int, default=2)
    args = parser.parse_args()
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{os.getenv("APP_API_PORT", "8000")}/health', timeout=2)
    except (urllib.error.URLError, TimeoutError, OSError):
        pass
    else:
        raise SystemExit('Stop the app before rebuilding its cached knowledge index.')
    paths = sorted((args.repo / 'episodes').glob('*/transcript.md'))
    if not paths:
        raise SystemExit('No source transcripts found; existing index retained.')
    revision_result = subprocess.run(['git', '-C', str(args.repo), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    revision = revision_result.stdout.strip() if revision_result.returncode == 0 else None
    previous_manifest = ROOT / 'data/chroma/corpus-manifest.json'
    if not revision and previous_manifest.exists():
        revision = json.loads(previous_manifest.read_text())['revision']
    if not revision:
        raise SystemExit('Cannot trace source revision; existing index retained.')
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='knowledge-build.', dir=data) as work:
        build = Path(work)
        rows = []
        episodes = []
        for path in paths:
            fm, turns = parse_transcript(path)
            if not turns:
                raise ValueError(f'No parsed turns: {path}')
            pieces = list(split_long_turns(turns, args.target_tokens))
            # Verify the split preserves the complete ordered dialogue.
            original = ' '.join(text for _, _, text in turns)
            restored = ' '.join(text for _, _, text in pieces)
            if original.split() != restored.split():
                raise ValueError(f'Dialogue lost during splitting: {path}')
            source_path = str(path.relative_to(args.repo))
            chunks = chunk_episode(fm, turns, path.parent.name, source_path,
                                   args.target_tokens, args.overlap_turns)
            combined = '\n'.join(chunk.text for chunk in chunks)
            if any(text not in combined for _, _, text in pieces):
                raise ValueError(f'Dialogue lost during chunking: {path}')
            rows.extend(asdict(chunk) for chunk in chunks)
            episodes.append({'source_path': source_path, 'guest': str(fm.get('guest', '')),
                             'title': str(fm.get('title', '')), 'parsed_turns': len(turns),
                             'chunks': len(chunks), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        chunks_path = build / 'chunks.jsonl'
        chunks_path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
        print(f'Coverage verified: {len(episodes)}/{len(paths)} episodes; {len(rows)} chunks; no dialogue omitted.', flush=True)
        index_path = build / 'chroma'
        subprocess.run([sys.executable, '-u', str(ROOT / 'rag/index.py'), '--chunks', str(chunks_path),
                        '--persist-dir', str(index_path), '--embedder', 'local-lexical'], check=True)
        from index import COLLECTION_NAME
        import chromadb
        client = chromadb.PersistentClient(path=str(index_path))
        collection = client.get_collection(COLLECTION_NAME)
        if collection.count() != len(rows):
            raise ValueError('Vector count mismatch; existing index retained.')
        actual = defaultdict(int)
        for offset in range(0, len(rows), 1000):
            batch = collection.get(limit=1000, offset=offset, include=['metadatas'])
            for metadata in batch['metadatas']:
                actual[metadata['source_path']] += 1
        if dict(actual) != {episode['source_path']: episode['chunks'] for episode in episodes}:
            raise ValueError('Indexed episode coverage mismatch; existing index retained.')
        manifest = {'source_repository': 'https://github.com/ChatPRD/lennys-podcast-transcripts',
                    'revision': revision, 'embedder': 'local-lexical', 'target_tokens': args.target_tokens,
                    'overlap_turns': args.overlap_turns, 'episodes_indexed': len(episodes), 'chunks': len(rows),
                    'chunks_sha256': hashlib.sha256(chunks_path.read_bytes()).hexdigest(),
                    'built_at': datetime.now(timezone.utc).isoformat(), 'episodes': episodes,
                    'coverage': {'source_episodes': len(paths), 'missing_episodes': [], 'dialogue_preserved': True}}
        (index_path / 'corpus-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        destination = data / 'chroma'
        backup = data / f'chroma-backup-{stamp}'
        if destination.exists():
            destination.rename(backup)
        try:
            index_path.rename(destination)
        except BaseException:
            if backup.exists():
                backup.rename(destination)
            raise
        chunks_path.replace(data / 'chunks.jsonl')
        print(f'Activated verified index: {len(episodes)} episodes, {len(rows)} vectors. Previous index: {backup}', flush=True)


if __name__ == '__main__':
    main()
