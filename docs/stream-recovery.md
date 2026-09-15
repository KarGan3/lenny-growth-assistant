# Recovery from stale knowledge-index state

The running backend on port 8000 reported `rag_index_count: null` while
Ollama, PostgreSQL and the evidence verifier were available. Its log identified
`Collection [45d7a38e-0095-42aa-b79e-b2a6525e8dd8] does not exist.` The backend
had cached the old collection across the knowledge-index replacement.

Restarting the backend reloaded the new index. `/health` then returned `ok`
with 40,551 indexed passages and all dependencies available. The backend is
running on its original port, with logs in `/tmp/lenny-backend-restarted.log`.

Chat processing now checks index availability before saving a user turn and
provides a 503 recovery message when loading/counting fails. The stream preserves
safe HTTP error details and logs unexpected failure types. The frontend keeps
the error message on the affected assistant bubble instead of replacing it
with generic unfinished-response text.

The screenshot's customer-acquisition-channel question completed through live
Pi/Ollama streaming in 48.87 seconds. Its final event was `done`, and both user
and assistant turns were persisted in labeled verification session
`1287a46d-7207-4fa3-8873-f2fbbac1550d`. The reply had five retrieved sources and
no automatic warnings. It remained incomplete, including a list starting at
item 2 and an introductory sentence without a clear antecedent; successful
stream delivery is not proof of answer quality.

Validation: 91 backend tests passed, including a regression that simulates
stale collection state, checks the streamed recovery message and verifies that
no user turn is saved. Frontend artifact-security test and production build
passed. Refresh the browser to load the updated error display.

Always stop the backend before replacing its index and restart afterward.
The preceding rebuild was launched in a sandbox whose localhost checks did
not see the host's running backend; the final live diagnosis and verification
were performed outside that sandbox. The preflight health check alone is not
a reliable guarantee that no backend is running in another network namespace
or on another port.

## Frontend-proxy follow-up

The user's subsequent error exposed a verification gap: frontends on ports
5173, 5174, 5175 and 5176 were proxied to backends on 8002, 8001, 8003 and
8004 respectively. The initial direct port-8000 verification did not exercise
any of those browser-facing routes. All four additional backends still had
stale collection state. They were reloaded with their original configuration.
Their original startup supervisors stopped dependent services on backend exit;
project-local PostgreSQL/Ollama and frontends 5173/5174/5176 were restored.

All four frontend `/api/health` routes subsequently returned `ok`, 40,551
indexed passages, and available model/database/verifier dependencies. The same
customer-acquisition question completed through `http://127.0.0.1:5173/api`
in 65.23 seconds with a final `done` event and two persisted turns. The labeled
verification session is `9e366302-72dc-4570-92b9-70f40cb5013d`; the runtime verification report
is `/tmp/lenny-proxy-recovery.json`.
This result verifies the frontend proxy transport, not just a direct backend
request. It does not certify model answer quality.
