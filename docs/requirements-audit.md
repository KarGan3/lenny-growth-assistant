# Assignment audit

The supplied DOCX is the requirements reference. This audit distinguishes implemented behavior, observed checks and external deliverables. A test pass is not proof of every possible model claim.

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Discovery: user, problem, success metric, assumptions, scope and trade-offs | `PRD.md` discovery, flows, acceptance criteria, risk table and implementation plan | Documented |
| FastAPI and clear contracts/validation/health/errors | `backend/app/main.py`, `schemas.py`, `routes/chat.py`; API/error tests; actual `/health` | Implemented and tested |
| Pi Coding Agent integration | Node bridge calls `createAgentSession`; real Pi/Ollama results and SDK localhost streaming test | Implemented and exercised |
| Independent new chats and contextual follow-ups | Chat API tests, retrieval topic tests; separate persisted sessions | Implemented; corrected Llama and Qwen pilots preserve the original Hila/GitLab retrieval topic and persisted replies; answer completeness still has limitations |
| PostgreSQL conversations, IDs, timestamps and user metadata | SQLAlchemy schema; actual evaluated conversation queried directly in PostgreSQL | Exercised on local PostgreSQL |
| Cloud provider integration | Configurable Anthropic/OpenAI Pi models; Anthropic request reached the API and returned billing failure | Integrated; funded generation unverified |
| Mandatory local Ollama demo and visible provider | Actual Pi/llama3.2:3b generation; real Chrome local-mode check | Exercised |
| Toggle and documented fallback | Config API/UI; explicit optional fallback; generated provider metadata tests; README | Implemented and tested |
| Transcript ingestion, chunks/index/refresh/source tracing | Pinned 303-episode, 23,702-chunk rebuild; manifest; refresh script; source URLs and retrieval tests | Rebuilt and tested |
| Strict grounded Q&A and unsupported-answer acknowledgement | Transcript-only default, evidence-only prompt, reference checks, citation-specific local entailment filtering, refusal tests | Implemented; classifier limits and factual review documented |
| Dedicated guide-derived Ship 30 skill | Reusable JSON principles and scoped essay writer; real approximate-length essay; failure logs | Implemented; latest 1,188-word generation saved; editorial limitations and heading fix documented |
| Hook/narrative/headings/bullets/bold/takeaway and grounded claims | Real essay and manual review under `docs/evaluation/`; source-scoped instructions | Formatting observed; factual quality is reviewed separately |
| Conversation-based Markdown and complete HTML/CSS | Actual saved source-backed answer, extractive conversion tool, explicit-new-topic Pi path, tests | Implemented; 441-word HTML/Markdown formatting retries persisted in approximately 1 ms; six saved artifacts checked in Chrome; failed earlier rewrite retained |
| Native adjacent artifact viewer | Actual saved-output Chrome reload/preview/code/copy/download check; screenshots | Exercised |
| Untrusted HTML isolation and explanation | Escaped server HTML, DOMPurify, empty sandbox, CSP; DOM and Chrome security tests; architecture/design | Implemented and tested |
| Reproducible setup and one-command startup | Locked dependencies, pinned Ollama/entailment weights, PG helper, corpus refresh, `setup.sh`/`start.sh` | Implemented; source extraction dependencies tested |
| Safe `.env.example`, no committed secrets | Strict source allowlist/credential scan; clean temporary Git repository and offline bundle clone | Reviewed local package; public commit pending |
| Observability and resilient failures | JSON app logs and safe provider diagnostics; missing-key/model/timeout/retrieval/DB tests | Implemented and tested |
| README, PRD, design, architecture and handoff | Root documents plus manual plan, verification, publishing and demo scripts | Present |
| Dedicated agent logs including failures/corrections | `agent-transcripts/` curated actual development record | Present; not claimed as a complete raw export |
| Meaningful automated tests and UI manual plan | Backend/RAG/DOM/Chrome suites and `docs/manual-test-plan.md` | Present and exercised within stated scope |
| Public GitHub source repository | Sanitized archive and cloneable Git bundle prepared; owner/repository and authentication needed | Pending external publication |
| Camera-enabled 2–3 minute YouTube demo | `docs/demo-script.md`; user recording/upload and actual URL needed | Pending external recording/upload |
| Fresh evaluator public clone using documented steps | Independent dependency installation tested; no actual public repository yet | Pending public-clone verification |
| Submission form | Actual repository/video URLs are not available | Pending |

Do not mark the assignment complete while public delivery or required verification remains missing. Current observed results and their limits are maintained in `verification.md`; actionable publication steps are in `publishing.md`.
