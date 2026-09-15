# Coding-agent development log (sanitized)

## Frontend/backend connection

User evidence: browser reported `ERR_CONNECTION_REFUSED` at localhost port 8000. Frontend initially used mock responses.

Actions: switched frontend to real API mode, configured Vite `/api` proxy rewrite, added session listing/deletion and a startup script that waits for backend health before starting Vite. Verified real chat through the frontend proxy.

## Agent integration and local demo

Requirement: use Pi Coding Agent or Claude Agent SDK, with mandatory Ollama demo.

Actions: installed pinned Pi SDK 0.68.0 and built a Node bridge using `createAgentSession`. Disabled coding tools/resource discovery. Installed project-local Ollama and pulled Llama 3.2 models. Installed a project-local PostgreSQL 16 cluster on port 5433 and migrated legacy SQLite rows while preserving the original file.

## Failed cloud access

A test that would export retrieved transcripts to Anthropic was rejected by automatic approval review; it was not bypassed. The user's subsequent API error reported insufficient Anthropic credits. Error handling now converts provider failures to actionable messages without Node stack traces. No successful paid cloud generation is claimed.

## Latency investigation and correction

Initial local generation was slow. Investigation found Pi resource loading reset compaction settings. Against the small local context, automatic compaction triggered an extra model request after each answer, using an unexpectedly large output budget. Correction: disable compaction and automatic retry AFTER resource loader reload, and enforce output limits on the final provider payload. A local SSE bridge test checks that only one generation request is made.

A 1B model and short context reduced latency but produced shallow answers. User feedback prompted restoring the stronger 3B model, five sources, larger evidence and output budgets. Streaming shows retrieval and text earlier. The larger model remains slower on CPU.

## Quality failures and correction

A retention test with the stronger model took approximately 116 seconds but copied a long quote and hit the token limit mid-sentence. The prompt was revised to paraphrase and aim for complete shorter conversational answers. The revised test finished in approximately 89.5 seconds; small-model quality limitations remained visible.

Retrieved sources contained overlapping chunks from the same episode, wasting evidence slots. Five-word shingle filtering now rejects strongly overlapping passages while preserving similarity rank and real chunk IDs. Automated coverage checks distinct evidence remains available.

## Assignment completeness audit

The DOCX was read as a requirements reference. Audit found the real backend lacked the Ship 30 skill and artifact output despite an existing mock viewer, and required PRD/design/architecture/handoff deliverables were missing.

Actions: implemented explicit writing routes, a guide-derived reusable Ship 30 rules resource, separate long-content budgets, Markdown artifacts and deterministic escaped complete HTML/CSS, saved artifact/warning JSON columns with additive migration, frontend artifact events, source-reference validation and visible essay length warnings. Empty/low-similarity retrieval refuses without generation. Added route, persistence, follow-up, empty retrieval, invalid-citation and HTML escaping tests, plus frontend DOMPurify/CSP tests.

## Verification process

A combined backend/RAG pytest invocation failed collection because both directories expose a `tests` package. Correction: run them independently with separate PYTHONPATH settings. Previous backend/retrieval checks passed after the correction. Final run evidence is maintained in `docs/verification.md`, rather than inventing results in this record.

Public repository publication and an actual camera-enabled YouTube video require the user's account/recording participation. Source package and demo instructions are prepared; no external delivery is claimed without evidence.

## Long-form second failure and source-scoped correction

The full-draft expansion/revision approach was tested with real Ollama and still failed: approximately 937 seconds, 1,050 words, and an unverified quotation. Real HTML and Markdown transformations did generate and persist, but the essay did not pass. This failure is not hidden as a successful deliverable.

Correction: use a short opening, five source-scoped practical sections and a takeaway, with small output budgets, a shared essay deadline, at most one correction per section, and up to two length additions. A scoped-reference check rejects a section that cites another retrieved source even when that number is globally valid. Automatic whole-essay rewrites were removed.

Other project edits appeared concurrently, introducing general-knowledge replies and a separately running backend. One patch initially matched the new helper's generation branch instead of the grounded branch and caused `NameError: name 'skill' is not defined`. Correction: move essay routing into the grounded handler. Ask the user to coordinate concurrent sessions and run tests on alternate ports rather than repeatedly stopping their app. General-knowledge behavior is preserved as an explicit opt-in; the assignment default stays transcript-only.

## Requested frontend palette

The user supplied #0F3040, #464858, #A56F63 and #D99B7F. Tailwind colors, surfaces, buttons, source accents and generated HTML use that palette. Small text uses teal/slate for contrast. Production build and Chrome palette/mobile/HTML isolation checks passed. A real screenshot is stored under `docs/screenshots/`.

## Source package review

The first secret scanner matched its own regex source; the pattern was corrected to match actual key syntax. Archive inspection also found an unintended backend-local index file; all data directories are now excluded. This source archive is separate from the read-only placeholder `.git` workspace. A clean temporary Git repository is used for review; no public push or external submission is represented as complete.

## Format success exposed semantic/topic problems

Real source-scoped generation produced and saved an essay of 1,170 words in 207.4 seconds, an HTML brief in 213.2 seconds and Markdown in 172.2 seconds. Format/persistence assertions passed. Direct PostgreSQL inspection confirmed six messages and three artifacts. Chrome verified reload recovery, preview, clipboard and downloaded content.

Manual review found three of ten sampled essay examples needed narrower wording or attribution. The Markdown transformation also drifted into unrelated teamwork/open-source sources because retrieval used the immediately preceding conversion command instead of the original topic; its valid citation numbers did not make the text reliable. Corrections: scan for the latest substantive conversation topic, skip intermediate conversions, replace history on explicit topic changes, and prohibit importing old citation numbers or guest attributions. Instructions now distinguish reported facts from suggested applications. Full guest-name metadata checking also catches two guests sharing a first name. Short documents use an 800-token cap instead of the full essay budget. New regression tests pass; the real conversation is rerun before claiming final success.

A test invocation without the local networking permissions stalled after the pure routing cases. It was stopped deliberately and rerun with localhost permissions; 20 content-skill checks passed. The full updated backend suite then passed 48 tests. A source-only package installed independent locked dependencies and passed its pre-change suites; this is not claimed as a public-clone/second-machine test.

## Generative audit failures and local classifier

The copied-sentence reviewer failed a real Gojek passage in 29.3 seconds with an unreliable JSON contract. Switching to compact draft-unit IDs produced valid JSON in 19 seconds but still retained the unreported engagement outcome. Those probes failed; valid JSON was not treated as factual success.

Replacement: pinned official quantized DeBERTa NLI weights, ONNX CPU inference, overlapping evidence windows with opening context, and citation-specific source validation. The actual passage check took 3.8 seconds, removed the unreported outcome and unsupported first-user instruction, and retained source-backed context. The model still misclassified two of nine manually labeled claims; its limits are recorded rather than claiming universal correctness. Proposed applications are distinguished from factual reports. Missing weights/failed checks flag drafts and withhold artifacts. Complete unit deletion cannot flip meaning by deleting words such as negation. Canonical transcript identities/URLs are appended to exports.

The updated source package passed 62 backend tests in its independent evaluator dependency installation. The classifier-enabled local conversation is evaluated separately; only its actual completed assertions count as a final functional pass.

## Speaker attribution and final presentation review

The first classifier-enabled Markdown still attributed an Albert Cheng retention statement to Crystal Widjaja. Speaker-owned passage checks and explicit source-state guards now reject that mismatch independently of the classifier score. Canonical episode metadata preserves supported roles; supported uncited units receive only verified numeric source identifiers. The subsequent real conversation saved a 1,207-word essay and two documents, with one artifact each and no warnings. Manual review found an empty heading and incomplete generated bibliography; cleanup removes these remnants while exports retain canonical sources. Repetition in the essay expansion remains a disclosed writing-quality limitation. The final worktree check passed 66 backend tests, retrieval/DOM checks and the production build before the small cleanup change.

The final extracted source package passed 67 backend tests using the evaluator copy's independently installed dependencies. Its corpus index was reused, so this does not claim a completely fresh public clone. Packaging now prunes local dependencies/models/data before filesystem traversal and excludes symlinks; the archive and Git bundle regeneration completed in 0.52 seconds and the offline clone verified.

Real ordinary Q&A correctly identified Airtable's activation milestone, but the follow-up called onboarding tactics components of that metric. Its citations/classifier status were insufficient to establish semantic correctness. The system instructions now explicitly preserve metric definitions and distinguish suggested tactics; a fresh live verification remains required.

The prompt-only fix failed its fresh 80.4-second follow-up. Inspection confirmed the cited passage discussed onboarding investments, not measured activation components. A definition guard now requires explicit measurement language in the guest's own turns; the real-answer probe removed the incorrect unit and retained supported advice. Two regression cases distinguish absent versus explicit definition evidence; the full backend suite passed 69 tests. A sequential runner for the documented ten-question set captures actual context and answers, with manual scores pending.

The documented factual run exposed incomplete PMF measurement coverage and a Hila Qu self-corrected-number/citation error. Review explicitly marks them as failures rather than treating grounded flags as success. Named-speaker retrieval now retains the requested guest's passages; the actual Rahul result includes the survey discussion and the retrieval suite passed 12 tests. The running baseline job was not restarted or silently relabeled as revised evaluation.

Explicit literal-detail checks reject withdrawn conversion windows and technical acronyms absent from the cited passage, allowing standard expanded aliases. The real Hila answer probe removed the known incorrect details, but also shortened the answer; useful complete answering still needs live review. Failed source checks now persist a clear refusal and clear citations rather than exposing the unsupported draft. The full suite passed 74 tests. A public Qwen2.5:3b pull prepares a comparison only; llama3.2:3b remains the configured default while the baseline continues.

The Crystal baseline answer misspelled Gojek as Gojaja. Literal named-organization anchors reject that typo independently of entailment scoring, while standard expanded aliases still pass. The final suite passed 76 tests. The Qwen model download remains active and is not represented as an evaluated improvement.

All ten baseline requests completed. The real follow-up lost GitLab context because “it” occurred in a second clause of the substantive parent question. Primary-clause tracking fixes this; nested parent headings are retained and stray marker-only lines removed. The complete suite passed 77 tests after the explicitly permitted retry of an approval-review timeout. The pilot reporter failed on MessageOut fields that actually belong to SessionOut; it now reads the real contract and is rerun separately. The model pull was terminal with unexpected EOF after service shutdown, then its resumed download completed with verified digest. No Qwen accuracy improvement or default switch is asserted yet.

The corrected Llama pilot completed three requests with actual session provider/model metadata and preserved Hila/GitLab follow-up retrieval. A wrong 40% reference motivated per-passage numeric/window anchoring and same-prose citation repair. The real probe repaired the reference but removed a valid introductory sentence. Repair whitespace was fixed and its adjacent-sentence regression passed. The full backend suite passed 83 tests after a developer general-knowledge setting was isolated in the test fixture; the first full run's one failure is recorded rather than omitted.

The separate Qwen2.5:3b local pilot uses cloud fallback disabled. Its first response took 81.6 seconds and omitted the PMF benchmark, with a wrong email-method citation. A real NLI probe scored that wrong passage highly and the actual survey passage poorly. This model/classifier combination is not promoted as an accuracy improvement. All ten original baseline answers now have manual source-review findings; no 90% benchmark result is claimed. The frontend palette uses exact requested slate surfaces and its production build passed. Submission packaging now excludes temporary atomic report files.

The Qwen three-question process finished with real persistence/model checks. It retained the correct GitLab milestone but left an incomplete PMF answer and a one-step follow-up; the source review records these rather than promoting Qwen. All three current Chrome palette/navigation/isolation checks passed. An independent corpus rebuild now runs in the extracted source copy; refresh checks its configurable API port. The final latest-code Llama essay/artifact conversation uses strict mode and disabled cloud fallback, with actual model/session metadata checked by the runner. Earlier generated artifacts are preserved separately while the final job remains live.

The independent corpus refresh exited 0 after cloning the pinned public source and rebuilding 303 episodes / 23,702 chunks with zero skipped episodes. Its chunk checksum and manifest settings match the original. All 83 backend tests passed against this new index using independently installed dependencies and an isolated test database; root-index reuse is no longer required for this check. Public-clone delivery and complete fresh-machine service setup remain separately unverified.

The latest strict local essay finished at 1,188 words with one saved Markdown artifact and no automatic warnings, in 458.8 seconds. Manual review still found generic opening/repetition and a missing Step 4 label. The actual cause was a sibling-level application subheading being interpreted as the end of an empty step during cleanup. The formatter now nests step-body headings; its actual-section replay, regression and complete 83-test suite passed. Saved outputs remain untouched as original evidence while HTML/Markdown follow-ups continue.

The final model-rewrite run failed its HTML artifact assertion; its failed report and original text are retained. Referential artifact requests now use a dedicated extractive conversation tool, keeping exact saved facts/citations and complete application bullets; explicit new topics retain Pi/retrieval. All 89 backend tests passed. A pytest-reserved parameter caused collection failure and was renamed. Artifact evaluation also clears stale output files rather than displaying an old HTML from a failed run.

Actual retries formatted and persisted 441-word HTML and Markdown artifacts in approximately 1 millisecond, without model regeneration. Conversion chains reuse the original answer. Real Chrome checks verified all six saved artifacts across generation/retries, including reload, previews and exact code/copy/download. The first browser attempt selected a duplicate-title chip incorrectly; persisted-order selection resolved it. Cloud labels now say API key missing/Key configured, and build passed. Local-model editorial/source limitations and external publication/video/billing dependencies remain explicitly open.

The final reviewed source extraction passed all 89 backend tests against its own independently rebuilt public index (3.39 seconds), plus Node security testing, production frontend build, Bash syntax and Python compilation. The sanitized source-only archive/bundle is regenerated; no public repository, funded cloud success, camera video or final form submission is claimed.

Startup port collision fixed: `start.sh` now selects the next free API/UI ports and prints their URLs. With ports 8000 and 8001 occupied, the real startup chose backend 8002 and frontend 5173. Backend `/health`, frontend `/`, and frontend `/api/health` all returned HTTP 200. Bash syntax passed; existing listeners were left running.
