# Lenny Growth Assistant

Ask product and growth questions in the React UI. FastAPI retrieves numbered
excerpts from Lenny's Podcast transcripts, runs a **Pi Coding Agent SDK** session,
and saves the question, generated answer, citations, and model attribution in
PostgreSQL. The frontend displays the answer and timestamped source links.

## Run the configured local demo

```bash
./start.sh
```

Open http://127.0.0.1:5173/. API documentation is at http://127.0.0.1:8000/docs.
Ctrl+C stops services started by the script; already running services stay running.

The local demo uses **Ollama / llama3.2:3b**, Pi Coding Agent, and PostgreSQL 16
at `127.0.0.1:5433`. The 3B model is the quality default. The installed
`llama3.2:1b` is faster but gives less reliable, less detailed answers. Restart
after changing the model ID.
Generation can take tens of seconds on CPU. The startup script preloads the
model. Replies stream into the UI as tokens arrive; sources and progress appear
before generation finishes. Retrieval filters strongly overlapping passages from the same episode before
selecting five sources, keeping the highest-ranked matches. The local prompt
uses up to 8,000 characters of evidence,
and a bounded history. Answers have a 512-token budget to explain reasoning and
practical steps with citations. The model has an 8,192-token context window.
These larger budgets improve detail but increase CPU generation time. Knowledge
is limited to the indexed transcripts; unsupported questions should be identified
as gaps, and cited claims should be checked against the source excerpts.

## Set up a fresh machine

The PostgreSQL helper targets Ubuntu 24.04 x86_64; the Ollama helper targets Linux
x86_64. Node.js 22.22.2+ or 24.15+, npm, Python 3.12, curl, and zstd are needed.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
(cd frontend && npm ci)
(cd backend/pi-agent && npm ci)
cp .env.example .env
cp frontend/.env.example frontend/.env
./setup-postgres.sh
./setup-ollama.sh
./start.sh
```

`setup.sh` builds the required index at `data/chroma`. To rebuild an index from
an already ingested chunks file:

```bash
.venv/bin/python rag/index.py --chunks data/chunks.jsonl --persist-dir data/chroma --embedder local-lexical
```

Query and indexing embedders must match. Do not switch `RAG_EMBEDDER` without
building a compatible index.

PostgreSQL is installed under `.local/postgres`, and its cluster is under
`data/postgres`. This development cluster uses local trust authentication and
listens on loopback. For hosted PostgreSQL, set `DATABASE_URL` to the supplied
authenticated connection string. The helper does not install a system service.

Existing SQLite chats were copied to PostgreSQL; the original `data/app.db` is
preserved. To repeat this migration safely after configuring PostgreSQL:

```bash
.venv/bin/python backend/migrate_sqlite.py
```

## Model configuration and switching

Edit the root `.env` and restart the backend to change model IDs or credentials.
No application code changes are required:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
LLM_FALLBACK_PROVIDER=
OLLAMA_CONTEXT_LENGTH=8192
LLM_TIMEOUT_SECONDS=180
LLM_MAX_OUTPUT_TOKENS=512
RAG_TOP_K=5
RAG_MAX_CONTEXT_CHARS=8000
```

The UI shows the selected provider and model. Its provider menu offers Ollama,
Anthropic Claude, and OpenAI; unavailable providers are disabled. Cloud providers
require their corresponding API key in `.env`. Cloud availability means a key is
configured; authentication and quota are validated when generating an answer.
Ollama availability checks that the configured model is installed.

`GET /config` reports provider options, selection, agent framework, fallback,
and request timeout. `POST /config/provider` accepts `{"provider_id":"anthropic"}`.
UI selections are held in backend process memory and reset to `LLM_PROVIDER` on
restart. Each chat request carries its selected provider, so another UI's selection
does not change an in-progress request. The demo runs one FastAPI worker.

### Fallback behavior

Fallback is **disabled by default**, ensuring the demo runs locally. Set
`LLM_FALLBACK_PROVIDER=anthropic` and configure its key to allow cloud fallback
when Ollama fails, or use `ollama` as fallback for a cloud primary.

The backend tries the primary once, then the configured different fallback once.
Pi automatic retries are disabled. Fallback use is logged, and the session stores
the provider/model that actually answered. The configured primary stays selected.
If both fail, the backend saves a clear model-unavailable reply with retrieved
sources; it does not fabricate a generated answer. Each attempt has its own timeout,
and the frontend timeout includes both attempts when fallback is configured.

## Streaming replies

`POST /sessions/{id}/messages/stream` emits NDJSON status, sources, text deltas,
the final answer, and a done event. Completed replies are saved before done.
The existing non-streaming endpoint remains supported. Stopping a reply cancels
the Node model process; a cancelled partial reply is not saved as a completed
answer. Fallback resets partial text before streaming a replacement answer.

## Agent integration

`backend/pi-agent/bridge.mjs` calls Pi's `createAgentSession` with in-memory
conversation, settings, and authentication. FastAPI passes the grounded system
prompt, retrieved excerpts, trailing chat history, provider, and model through
stdin to the Node bridge. Pi owns the agent session and provider-backed generation
for **both local and cloud providers**. Coding tools and project resource discovery
are disabled because this is a transcript-grounded assistant with writing routes.

The package is pinned and locked in `backend/pi-agent/package-lock.json`.
See the [official Pi SDK documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md).
The Python Anthropic/OpenAI/Ollama adapters are used for readiness checks;
generation goes through Pi, rather than the previous direct generation loop.

## Validation

```bash
PYTHONPATH=backend RAG_PERSIST_DIR=./data/chroma RAG_EMBEDDER=local-lexical .venv/bin/python -m pytest backend/tests -q
(cd frontend && npm run build)
```

Backend tests isolate persistence in SQLite and stub generation. The running
demo uses PostgreSQL and real Pi/Ollama generation. Cloud generation requires
evaluator credentials and has not been verified against a live paid endpoint here.

## Complete setup workflow

On Ubuntu 24.04 x86_64, install Python 3.12 with venv support, Node.js 22.22.2+ or 24.15+, npm,
git, curl, zstd and dpkg-deb. Ubuntu's package repositories must provide
PostgreSQL 16. Then run:

```bash
./setup.sh
./start.sh
```

`setup.sh` installs locked Python and Node dependencies, copies safe environment
examples only when missing, installs project-local PostgreSQL/Ollama, pulls the
configured local model and builds a reproducible transcript index. It does not
overwrite your keys. Downloads need internet and several GB of free disk space.
The helper pins [Ollama 0.34.0](https://github.com/ollama/ollama/releases/tag/v0.34.0);
set the shell variable `OLLAMA_VERSION` intentionally to test another release.
No application code changes are necessary. On other systems, install PostgreSQL
and Ollama yourself and configure their URLs; the helper binary setup targets
Ubuntu/Linux x86_64. Run from the project root.

## Writing skills and artifacts

Ask a normal question, “Draft a Ship 30 for 30 essay on activation,” “Turn that
into a Markdown document,” or “Make an HTML one-pager of retention.” The validated
API `skill` field can explicitly select `grounded_qa`, `ship_30_for_30`,
`markdown_artifact`, or `html_artifact`. Keyword routing provides the normal UI path.

Requests such as “turn that into HTML” create an extractive brief from the saved
source-backed answer. The tool selects complete paragraphs and practical bullets,
preserves their source identifiers, and formats Markdown or self-contained HTML
without another model call. Conversion chains use the original answer rather than
repeatedly shortening an earlier brief. An explicit new topic uses fresh retrieval
and Pi generation; its citation numbers belong to those new excerpts. An unrelated
refusal or general-knowledge answer cannot become a source-backed artifact.

The reusable Ship rules are in `backend/app/skills/ship_30_for_30.json`, derived
from the assignment's [Ship 30 guide](https://www.ship30for30.com/post/how-to-start-writing-online-the-ship-30-for-30-ultimate-guide).
The guide informs reader specificity, expert curation, actionable organization
and outline-first writing. The assignment adds the approximately 1,250-word
format. Essays target 1,100–1,400 words. The writer produces an opening, five
source-scoped practical sections and a takeaway, with small per-section model
budgets. Source labels are assigned from the actual input excerpt, and completed
paragraphs/sentences are trimmed to each section budget. A section may receive one reference correction; up to two additions
address short output. All writing shares a 600-second essay deadline; remaining
length or reference issues appear as warnings.

Content generation has separate optional settings:

```dotenv
CONTENT_MAX_OUTPUT_TOKENS=2400
DOCUMENT_MAX_OUTPUT_TOKENS=800
CONTENT_TIMEOUT_SECONDS=600
LLM_TEMPERATURE=0.2
RAG_MAX_HISTORY_CHARS=3000
```

Each provider attempt uses its corresponding timeout; essay completion permits
bounded source-scoped writing and reference corrections. The essay shares its
content deadline; normal answers permit one reference correction. Short HTML/Markdown
documents use the smaller document cap rather than the full essay budget. Essays can take several
minutes on CPU. The frontend extends its timeout for content routes. Artifacts
are saved with the message and recover after reload. A pinned local CPU entailment
classifier checks reported claims against their cited passages and can remove
unsupported complete sentences. Missing weights or failed checks flag drafts and
withhold artifacts. Proposed applications remain distinct from reported outcomes.
The checker adds seconds rather than another long model generation, but does not
prove every claim and can remove valid text. Exported artifacts include canonical
transcript identities and URLs. Markdown renders natively;
HTML one-pagers use a generated grounded Markdown document assembled into a
complete escaped HTML/CSS page. The viewer supports preview, source, copy and
download. In-app HTML is sanitized, placed in an empty iframe sandbox and protected
by CSP against scripts, forms and external requests. See `architecture.md` for
permissions and limits. Copied/downloaded files are outside the preview sandbox.

## Knowledge refresh and provenance

The source is [ChatPRD's public transcript repository](https://github.com/ChatPRD/lennys-podcast-transcripts).
The default pinned source revision is recorded in `scripts/refresh-knowledge.sh`.
After stopping the app, run:

```bash
./scripts/refresh-knowledge.sh
```

For an intentional update, set `TRANSCRIPT_REVISION` to your selected commit.
The pipeline parses metadata/timestamped speaker turns, creates approximately
350-token chunks with two overlapping turn segments, and builds local TF-IDF/SVD vectors.
Long speaker turns are split into bounded passages while preserving all words,
speaker labels and source timestamps. Timestamp-only continuations retain the
speaker and update the timestamp.
It builds separately before swapping indexes, retaining a previous index backup.
`data/chroma/corpus-manifest.json` records revision, source, hash, counts, embedder
and build time. Source paths and video timestamps remain traceable. Every source includes the
actual transcript URL at the indexed revision; uncertain upstream title/video
metadata uses this authoritative file link. Data/model
files and the third-party clone are regenerated rather than committed.

To rebuild from the complete existing local source archive without fetching data,
stop the app and run:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -u scripts/rebuild-knowledge.py
```

This checks dialogue preservation, every source episode, vector counts and
per-episode indexed counts before activating the new index. Its manifest includes
the complete episode catalog used for named-guest retrieval. Restart the app after
rebuilding to reload cached retrieval state. This rebuild fits the retrieval
vectorizer and index; it does not train or fine-tune the Ollama language model.

## Troubleshooting

| Symptom | Action |
|---|---|
| Connection refused / empty sessions | Keep `./start.sh` running, use port 5173 for UI, check `/health` and terminal output. |
| Ollama unavailable | Run `./setup-ollama.sh`, verify the configured model appears in `/api/tags`, and restart. |
| Slow CPU answers | Check active model and timing logs. 3B improves capability over 1B but costs latency; long essays use the content budget. |
| Anthropic low credits | Fund the API account or keep Ollama selected. A key alone does not establish billing availability. |
| Missing cloud option | Configure its key/model and restart the backend. Never put API keys in frontend Vite variables. |
| Retrieval unavailable | Stop app, run knowledge refresh, and verify corpus manifest/query embedder match. |
| Source verifier unavailable | Run `.venv/bin/python scripts/setup-evidence.py`; check `evidence_available` in `/health`. Missing/failed checks withhold downloadable artifacts. |
| Database unavailable | Check PostgreSQL port 5433, configured DATABASE_URL and `.local/postgres/server.log`; run setup helper. |
| Artifact missing | Unsupported evidence, invalid references or a model failure prevents artifact creation. Check visible warnings and logs. |
| Essay too short/long | Inspect visible word-count warning and request a revision; small-model format adherence is not guaranteed. |
| Port already used | `./start.sh` chooses the next free API/UI ports and prints their URLs. You can choose starting ports with `APP_API_PORT=8001 APP_UI_PORT=5174 ./start.sh`; existing listeners stay running. |

JSON backend logs include retrieval/generation timing, provider failure/fallback,
quality warnings and database failures. Avoid recording terminals containing
credentials. The local dev database uses loopback-only trust authentication; use
authenticated database connections and access control for a hosted deployment.
Backup chats with PostgreSQL `pg_dump` before schema/deployment changes. Preserve
`.env` privately; do not include it in bug reports or public source.

## Tests and evaluator handoff

After knowledge setup:

```bash
./scripts/check.sh
(cd frontend && npm run test:e2e)
```

The second command needs the running demo and installed Google Chrome. It covers
browser rendering and isolation, not model factual accuracy. Fast deterministic
backend tests use isolated SQLite and stub generation; the recorded local
product evaluation uses PostgreSQL, Pi and real Ollama. Run
`.venv/bin/python scripts/evaluate-local.py` deliberately to generate an actual
long essay and both artifact types; this can take several minutes and saves an
evaluation session. Model word-count warnings should not be mistaken for passes.

Read [PRD](PRD.md), [design](design.md), [architecture](architecture.md),
[manual UI and factual plan](docs/manual-test-plan.md),
[verification evidence](docs/verification.md), [demo script](docs/demo-script.md),
and [submission checklist](docs/submission-checklist.md).
Sanitized coding-agent development records are in `agent-transcripts/`.

To extend writing behavior, add a validated skill route/rules and tests. To add a
provider, implement readiness, Pi model registration and configuration visibility.
To change retrieval, rebuild an index with the matching embedder and evaluate
claim support. To prepare a public source archive with secrets/data excluded:

```bash
./scripts/prepare-submission.sh
```

The archive and cloneable Git bundle are under `submission/`; see
[publishing instructions](docs/publishing.md). Publication and actual camera-enabled video
URLs must be recorded before submission. No paid cloud success or public delivery
is claimed until verified.

The submitted demo defaults to `ALLOW_GENERAL_KNOWLEDGE=false`, preserving
transcript-only answers. Optional general replies require explicitly enabling
this setting; they are labeled, contain no fabricated citations, and cannot
produce artifacts. Keep the default for assignment evaluation.
