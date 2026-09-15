# Lenny Growth Assistant — Frontend

Vite + React + Tailwind chat UI for the Lenny Growth Assistant. Chat with
session history, a live LLM-provider toggle (cloud ⇄ local/Ollama), grounded
source citations, and an in-app **Artifact Viewer** that renders Markdown and
**sandboxed** HTML/CSS beside the conversation.

## Run it

```bash
npm install
npm run dev          # http://localhost:5173
```

The frontend uses the real backend by default. Start the backend from the project root:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:5173/ to ask questions. Vite forwards `/api` requests to
`http://127.0.0.1:8000` and removes the `/api` prefix. The backend retrieves
transcripts, generates an answer, and stores the question, answer, and citations.
The UI shows source links and progress immediately, then renders text as the
Pi agent generates it. Existing chats load from the database.

For local development, the root `.env` can use `DATABASE_URL=sqlite:///./data/app.db`
and `RAG_PERSIST_DIR=./data/chroma`. Run the backend from the project root.
For the project-local Ollama installation, run `./setup-ollama.sh` once from the
project root, then `./start.sh` to start Ollama, the backend, and the frontend.
The local configuration uses `llama3.2:3b` for CPU operation. Without a running model, the backend returns
an availability message with retrieved sources instead of a generated answer.
To use demo data instead, explicitly set `VITE_USE_MOCK=true`.

## Backend contract

The real adapter uses:

| Method | Backend path | Purpose |
|---|---|---|
| GET | `/health` | Database, RAG, and model availability |
| GET | `/sessions` | List chats |
| POST | `/sessions` | Create a chat |
| GET | `/sessions/{id}/messages` | Load messages and citations |
| POST | `/sessions/{id}/messages` | Retrieve sources and generate an answer |
| DELETE | `/sessions/{id}` | Delete a chat and its messages |
| POST | `/sessions/{id}/messages/stream` | Stream answer text and source events |

The provider menu switches between Ollama, Anthropic Claude, and OpenAI through
`/config/provider`. Set cloud API keys and model IDs in the root `.env`, then
restart the backend. See the root README for PostgreSQL, Pi agent integration,
and fallback behavior.

## Artifact security

Generated HTML is treated as untrusted and rendered through three layers
(`src/lib/sanitize.js` + `ArtifactViewer.jsx`):

1. **DOMPurify** strips scripts, event handlers, and dangerous elements.
2. A **fully sandboxed `<iframe>`** (`sandbox=""`): unique origin, no scripts,
   no forms, no same-origin, no top-navigation.
3. A **strict CSP** inside the iframe (`default-src 'none'`) blocks all network
   requests, so even sanitized markup cannot exfiltrate data via images/fonts.

Chat and Markdown artifacts never render raw HTML (react-markdown without
`rehype-raw`), so they are safe by construction.

## Structure

```
src/
  api/        httpClient · realApi · mockApi · index (adapter switch)
  hooks/      useChat (state + streaming) · useMediaQuery
  lib/        Markdown · sanitize (HTML isolation)
  components/  Sidebar · SessionList · ProviderToggle · ChatPanel ·
              MessageList · MessageBubble · Sources · Composer ·
              ArtifactViewer · EmptyState · TypingIndicator
```

## Docker

`Dockerfile` builds static assets and serves them via nginx, which proxies
`/api` to the `backend` service (see `nginx.conf`, `proxy_buffering off` for
streaming). Wire it into the root `docker-compose.yml`.
