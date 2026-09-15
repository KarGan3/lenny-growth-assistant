# Data directory (not committed)

This folder is populated by running the ingestion pipeline — nothing here
is checked into git, matching the assignment's "no committed secrets /
sensible project structure" guidance (a 480MB vector index and a full
clone of the transcripts repo don't belong in source control either).

From the repo root:

```bash
git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git rag/data_repo
python3 rag/ingest.py --repo rag/data_repo --out data/chunks.jsonl
python3 rag/index.py --chunks data/chunks.jsonl --persist-dir data/chroma --embedder onnx-minilm --reset
```

(`--embedder local-lexical` also works with zero network access — see
rag/index.py — and is what this was developed and tested against.)
