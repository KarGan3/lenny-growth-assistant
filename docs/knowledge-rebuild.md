# Complete local knowledge rebuild

The existing archive contains 303 transcript files at revision
`be8ab89a890a833cbba2c892178f823fff178c65`. All 303 were already represented
in the old chunk file; no missing local episodes or parse failures were found.
This audit does not establish that the pinned archive includes every episode
ever published, or that the remote repository has no newer transcripts.

The old turn-aligned chunks targeted 350 estimated tokens but had a median of
468 and a maximum of 4,693; 1,963 exceeded 1,000 estimated tokens. With the
agent's bounded context, oversized passages could lose relevant trailing
details. Long turns are now split at sentence/word boundaries. All text words
are retained and split segments keep the original speaker and timestamp.
Timestamp-only continuations now update the timestamp without changing the
speaker, and two-component timestamps are normalized to HH:MM:SS.

The final activated rebuild fits a new TF-IDF/256-dimensional SVD model on
all regenerated passages and creates a new Chroma index. It contains:

- 303 source episodes and 303 indexed episodes, with none missing.
- 62,596 parsed timestamped dialogue segments.
- 40,551 vectors, compared with the old 23,702.
- Median chunk size 280 and maximum 350 estimated dialogue-text tokens.
- Per-episode source hashes and actual indexed chunk counts in the manifest.

Speaker labels add extra characters beyond the dialogue-text token estimate.
Two overlapping turn segments are retained where the window size permits.
The rebuild verifies ordered word preservation during splitting, inclusion of
every split segment in chunks, vector count, and actual per-episode vector
counts before activation. Previous indexes remain in ignored backup folders.

Named-guest retrieval uses the entire manifest episode catalog so a requested
guest need not first appear in unrestricted vector search results. Actual
Rahul Vohra and Brian Chesky searches returned five passages from the requested
guest. The broad successful-launch query still retrieved weak evidence;
complete indexing is not proof of successful example selection or model
answer completeness. No new end-to-end model generation or factual benchmark
pass is claimed.

Validation: the final combined backend/RAG suite passed 104 tests in 4.03
seconds outside the sandbox. The sandboxed API run stalled in Starlette's
threaded TestClient; its stalled processes were stopped. Python compilation
and refresh-script Bash syntax checks passed.

Stop the app, then rebuild from local data with:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -u scripts/rebuild-knowledge.py
```

Restart with `./start.sh` to reload cached retrieval state. Remote refresh
continues through `scripts/refresh-knowledge.sh`, which now calls the verified
rebuild after checking out the requested source revision. Neither operation
trains or fine-tunes the Ollama language model's weights. Each response still
receives selected passages (default k=5), rather than all episodes at once.
