# Lenny Growth Assistant — Product Requirements

## Discovery brief

**User and job.** A product manager, founder or growth practitioner needs to turn expert podcast discussions into decisions and reusable team briefs. Searching long transcripts and copying advice into separate documents is slow; generic chatbot answers are difficult to verify.

**Outcome.** Ask a product question, inspect the evidence, refine it in an independent conversation, and generate a readable essay or brief beside the chat.

**Success metrics.** On a 10-question transcript-backed evaluation set, target at least 90% of substantive claims supported by the cited excerpt and zero fabricated quotations. Target 100% source-link correctness, session separation and saved-artifact recovery. Measure median and p95 time to first token and final reply on the evaluator's hardware. Aim for first text within 40 seconds for a warm 3B CPU model; long essays have a separate 600-second attempt budget. These are acceptance targets, not claimed achieved metrics.

**Assumptions.** This is a single-user local internal demo, without authentication. The public transcript repository is the only factual authority. Local processing is the default; cloud processing requires intentional provider selection or configured fallback. CPU inference is acceptable. A long-form essay may take several minutes. “Ship 30” means applying the linked guide's writing principles to the assignment's approximately 1,250-word format; the guide is not itself a demand for 1,250 words.

**Included.** FastAPI, Pi SDK, PostgreSQL, streamed chat, source links, four application skill routes, saved Markdown/HTML artifacts, isolated HTML preview, provider configuration, scripts, tests and operational handoff.

**Excluded and why.** Authentication, multi-tenant permissions, automatic publishing, autonomous coding tools, analytics collection and hosted deployment are excluded to keep a local evaluation understandable. Production use needs authenticated PostgreSQL, access control, rate limits, backup automation and deployment hardening.

## User flows

1. Start the application and see the active model. Start a new chat or reopen a saved chat.
2. Ask a question; see retrieval progress and sources, then streamed text.
3. Ask a contextual follow-up. The session's trailing history and preceding topic inform the answer and retrieval.
4. Request a Ship 30 essay, Markdown document or HTML one-pager. Read streamed content; open the resulting artifact automatically beside the chat. Preview, copy or download it. Reload and reopen the saved artifact.
5. Select a configured cloud provider if desired. Unconfigured options are disabled. Billing/authentication errors produce actionable replies without stack traces.
6. Stop generation, start another session or delete a session.

## Acceptance criteria

- A fresh Ubuntu 24.04 x86_64 evaluator runs documented setup and `./start.sh` without editing application code.
- Chats, timestamps, user metadata, citations, warnings and artifacts persist in PostgreSQL. Session history is independent.
- Answers use numbered transcript citations. In the submitted default configuration, empty/very low similarity retrieval refuses without a model call for every skill. An optional, explicitly enabled general-knowledge mode applies only to plain Q&A; those replies are marked unsourced and carry no citations. Content-generation skills always require transcript evidence. Invalid or absent citation numbers flag the draft; this is a reference check, not proof of factual entailment.
- The essay route loads reusable guide-derived rules and aims for 1,100–1,400 words with a hook, consistent headings, bullets, selective bold and a useful conclusion. Length deviations are visible rather than disguised.
- Markdown and complete HTML/CSS artifacts are produced by the real API, rendered inside the product, and recovered after reload.
- HTML cannot execute scripts, submit forms, navigate the parent, access parent storage or fetch external resources in the preview.
- Missing keys, model outages/timeouts, missing retrieval and database failure have understandable states. Model errors do not become artifacts.
- Automated critical-path checks pass, and the manual evaluation plan is recorded honestly.

## Risks and trade-offs

| Risk | Decision and limit |
|---|---|
| Hallucination | Evidence-only instructions, source references, reference validation and manual claim review. The submitted default refuses insufficient retrieval for all skills. General-knowledge mode is explicit opt-in for plain Q&A only. A small model can still misattribute or overgeneralize. |
| Retrieval quality | Local TF-IDF/SVD avoids extra model downloads; overlapping same-episode passages are filtered. Semantic embedding migration requires rebuilding the index. |
| CPU latency/quality | 3B is more capable than the installed 1B but slower. Streaming and preload improve experience; long writing has independent limits. |
| Data leakage | Local Ollama is the default, cloud fallback is disabled. Choosing cloud sends excerpts and trailing history to that provider. Logs exclude prompt bodies and keys. |
| Unsafe rendering | Escaped server HTML, DOMPurify, an empty iframe sandbox and restrictive CSP. Downloaded files are separate from the in-app sandbox. |
| Availability | Each attempt has a timeout; optional fallback is explicit. Paid cloud success depends on valid funded credentials. |
| Dev database security | Loopback-only trust authentication simplifies local setup; never expose this cluster publicly. |

## Implementation and handoff

Stages: conversational core → quality/routing → reusable writing and artifacts → rendering safety → reproducible corpus/setup → documentation and evaluation → public repository and camera-enabled video.

Current implementation and honest verification evidence are tracked in `docs/verification.md`; remaining submission actions are in `docs/submission-checklist.md`.
