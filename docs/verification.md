# Verification evidence

This file records observed checks, not assumed deliverable completion.

## Environment

Ubuntu 24.04 x86_64, Python 3.12, Node.js 24, local PostgreSQL 16 on port 5433, Ollama 0.34.0, llama3.2:3b with 8192-token context. CPU inference on an Intel i5-11320H; the NVIDIA driver is unavailable.

## Completed checks

- Full ingestion/index rebuild: pinned public source revision `be8ab89a890a833cbba2c892178f823fff178c65`, 303 indexed episodes, 23,702 chunks, no skipped episodes. Corpus manifest records SHA256 and build time.
- Current worktree backend suite: 77 tests passed, including route isolation/persistence, Pi streaming/output limit/no compaction, errors/fallback, source-scoped essays, short-document caps, chained topics, canonical exported sources, classifier availability and citation-specific validation.
- Retrieval/ingestion suite: 11 tests passed.
- Frontend DOM rendering/security suite: 2 tests passed.
- Real Chrome browser checks: 3 ordinary checks passed, covering real local provider UI/mobile navigation, the requested palette, and HTML styling/script/form/network isolation. An additional explicitly selected real-output check passed: all three actual local artifacts reopen after reload, preview, copy and download with matching content.
- Production frontend build, Python compilation and bash syntax checks passed passed in the final check before the presentation cleanup.
- Existing PostgreSQL conversations survived additive artifact/warning JSON column migration.
- PostgreSQL was queried directly for the evaluated conversation: six messages, three assistant outputs and three artifact JSON objects, no warnings.
- Fresh source extraction installed its own locked Python and both Node dependency sets. Its updated packaged backend suite passed 67 tests; frontend DOM tests and production build passed there too. These checks reused the verified public corpus index, so they do not prove a completely independent setup or a public clone.

## Failures found and corrected

The first real local essay stopped at 619 words and was flagged. Bounded evidence-based expansion now addresses this. A subsequent Markdown transformation omitted references and produced no artifact; bounded reference repair now addresses that. Overlapping chunks and incorrect upstream video/title metadata were found; deduplication and authoritative transcript links address them. An older manually launched reload backend conflicted on port 8000; it was confirmed to belong to this project and replaced, and occupied-port checks were added.

## Final local evaluation

The pre-topic-fix conversation passed format/persistence assertions: essay 1,170 words / 207.4 seconds (first text 7.5 seconds), HTML 530 words / 213.2 seconds, Markdown 524 words / 172.2 seconds. Browser and PostgreSQL checks passed. Manual content review then found attribution/generalization issues and topic drift in the second conversion; those successful format checks are not represented as semantic accuracy checks.

The topic-fixed pre-classifier conversation also passed format/persistence: essay 1,237 words / 258.1 seconds, HTML 607 words / 189.0 seconds, Markdown 467 words / 181.7 seconds. Generated sources remained on activation. A copied-sentence Pi reviewer failed its JSON contract; its compact-ID replacement still missed a known unreported outcome. Neither is claimed as a successful accuracy layer.

The replacement local quantized entailment model rejected the actual essay's unreported engagement outcome and unsupported first-user instruction in a 3.8-second passage check. It retained supported Gojek context. Nine manually labeled source claims were also probed: seven decisions matched labels, with a false positive for an inactive-team generalization and a false negative for an unqualified north-star claim. This small calibration check is not the PRD's 10-question factual benchmark or proof of every claim. The classifier is conservative and fallible; human review remains required.

The post-speaker-guard conversation completed through the isolated UI on port 5174: essay 1207 words / 284.1 seconds (first text 13.5 seconds); HTML 379 words / 220.4 seconds (first text 33.9 seconds); Markdown 250 words / 223.6 seconds (first text 32.5 seconds). All three saved artifacts have no warnings. Manual review found an empty heading and partial generated bibliography; document cleanup now removes these presentation leftovers and exports canonical transcript references. The essay also repeats some advice in its bounded expansion; this remains a writing-quality limitation, not a claimed perfect narrative. Chrome saved-output checks passed for this exact conversation, and direct PostgreSQL inspection confirmed six messages, three assistant outputs and three artifacts with no warnings. The final presentation-cleanup regression and backend suite passed 67 tests. The first real Q&A answered Airtable's week-four multi-user activation milestone with supporting citations (140.1 seconds, first text 112.9 seconds). The persisted follow-up completed in 141.3 seconds but manual review found it conflated onboarding tactics with metric components. Instructions now distinguish definitions from proposed tactics; that correction needs a fresh live check. The unsupported weather question completed in 50.2 seconds, correctly refused with no citations; the real script confirmed distinct persisted chats (four messages versus two at that point). These observations do not establish the 90% factual benchmark. Earlier approaches and pre-fix review remain clearly labeled.

## External/unverified items

No paid cloud generation has succeeded: Anthropic billing rejected access for insufficient credits, and OpenAI is unconfigured. Public repository and actual camera-enabled YouTube video URLs are pending. The workflow has rebuilt the corpus and validated the existing machine, but a fresh PUBLIC clone on a second machine has not yet been tested.

## Metric-definition correction and documented benchmark

The prompt-only metric correction failed: a fresh follow-up still called onboarding tactics metric components (80.4 seconds). Explicit measurement-language anchoring in the guest's own turns now rejects that unsupported definition, independently of a high entailment score. A probe using the actual failed answer and its real passages removed the offending unit while retaining two supported recommendations; positive/negative regression cases pass. The full worktree backend suite then passed 69 tests. The documented ten-question local run is in progress; its answer/context records require manual claim-by-claim scoring before any factual benchmark claim.

The first benchmark answer was supported but incomplete; the second contained a self-corrected-number error and a wrong citation. These are recorded in `evaluation/factual-review.md`, not treated as factual passes. Named-speaker retrieval now queries that guest's passages rather than filling slots with unrelated episodes; the revised real Rahul retrieval includes the disappointed-user survey passage and all 12 retrieval tests pass. The active ten-question baseline uses the earlier retrieval code and remains valid as baseline evidence; revised live checks are pending.

## Literal-detail and failed-draft handling

Explicit acronym anchors (with standard expanded aliases) and self-corrected time-window checks now reject the Hila Qu PR/citation and 30-day conversion errors. A probe against the actual baseline answer/captured excerpts removed the incorrect units; conservative filtering also shortened the answer, so this is not a claim of full answer usefulness. Failed reference/audit checks now return a clear verification refusal without unsupported draft text, citations or artifacts. The complete backend suite passed 74 tests after this change. A Qwen2.5:3b download is being prepared for a bounded local-model comparison; no default switch or improved-accuracy claim has been made.

A further baseline answer misspelled Gojek as Gojaja. Literal organization anchors now reject names absent from the cited passage/metadata; expanded standard acronyms remain allowed. Both correct/incorrect company cases and expanded-alias cases pass, and the final backend suite passed 76 tests. Qwen download remains live; no alternate-model generation has been claimed.

## Completed baseline and corrected comparisons

All ten baseline requests/persistence assertions completed; their original answers and contexts are preserved in `evaluation/baseline-factual-report.json`. Question 9 drifted into teamwork because the original activation/GitLab question used “it” in its second clause and was wrongly skipped as referential. Topic tracking now checks the primary clause; its regression and the full 77-test backend suite pass. Cleanup preserves parent headings and removes citation-only leftovers. One test approval review timed out before execution; its explicitly permitted retry succeeded.

The corrected pilot reporter initially failed after a successful API reply because provider/model fields belong to SessionOut, not MessageOut. The reporter now reads the actual session contract and is rerun with separate output. Qwen pull initially ended with unexpected EOF when the shared Ollama service stopped; its resumed download completed and verified its SHA256 digest. Qwen generation has not yet been compared, and the default remains llama3.2:3b.

## Citation repair and model comparison — 14 September

The corrected three-question Llama pilot completed with saved replies and actual session provider/model metadata. Its timings were 36.4, 127.7 and 150.7 seconds; the activation follow-up now retrieves the original Hila/GitLab topic. Its PMF benchmark still had a wrong reference. Per-passage percentage and conversion/retention-window checks now prevent unrelated passages from supporting those literal details. When another passage verifies exactly the same prose, the audit can replace only its numeric reference; otherwise it removes the unit. A real probe (`evaluation/citation-repair-probe.json`) corrected the 40% reference to passage 3 but also removed a valid introductory sentence. This is a demonstrated false negative, not a fully successful answer.

The backend suite passed 83 tests after strict-mode isolation and repair whitespace handling. The initial full run had one failure because a developer's `.env` enabled general knowledge; the fixture now explicitly selects strict mode. The first restricted-sandbox run stalled and was explicitly interrupted; the permitted host run completed. The adjacent-sentence repair regression then passed in the 28-test evidence-audit suite.

A separate local API on port 8002 is comparing Qwen2.5:3b through Pi, retrieval and PostgreSQL with cloud fallback disabled. Its first answer completed in 81.6 seconds (first text 43.3 seconds), described the survey but omitted its measurement benchmark, and cited the email-method passage rather than the survey passage. A real classifier probe scored that wrong passage 0.876 and the actual survey passage 0.013: the classifier can produce both false positives and false negatives. The model is not promoted to the default, and neither model has demonstrated the PRD accuracy target. The completed ten-question baseline source review is in `evaluation/factual-review.md`.

The frontend now uses the requested deep teal background, exact slate card/input surfaces, terracotta and peach accents. Its production build passed. Packaging excludes atomic `.tmp` files as well as secrets and runtime data.

The regenerated 156-file source archive and Git bundle passed bundle verification and offline cloning. The packaged source was extracted over the independent locked-dependency installation under `/tmp`; all 83 backend tests passed there in 4.32 seconds. This check reused the root public transcript index and did not rebuild it, so it does not establish fresh public-clone setup. The running Qwen evaluation may add further report records after this package snapshot; regenerate before publication.

The independent frontend installation passed its current Node artifact-security test file and production build. The worktree retrieval suite passed all 12 tests, and Bash syntax checks passed for startup/setup/refresh/submission scripts. These checks establish source/test/build behavior, not the missing public publication or camera video.

## Latest browser and completed Qwen pilot

Three real Chrome tests passed against port 5174: all four exact requested palette colors (page, composer, button and hover), local-mode mobile navigation, and untrusted HTML preview isolation. The previous palette test expected teal heading text from the earlier light theme; it now checks the current requested dark background and slate surfaces.

The Qwen pilot process completed with exit 0 and three saved replies/provider/model assertions. Timings were 81.6, 105.6 and 122.6 seconds. Its activation milestone was correct, but its PMF answer was incomplete/mis-cited and its follow-up retained only one step after filtering. `evaluation/qwen-review.md` records the actual comparison limits; the default remains Llama.

The final latest-code Llama essay/HTML/Markdown evaluation is running on a separate API at port 8003 with strict transcript mode and cloud fallback disabled. Its runner now verifies actual session provider/model metadata. Previous generated outputs are preserved with the `before-citation-repair-` prefix. A separate independent corpus refresh is rebuilding all public transcripts rather than reusing the root index. The refresh readiness check now honors `APP_API_PORT`, so unrelated port-8000 apps do not prevent an isolated rebuild. Neither live job is yet claimed complete.

## Independent public-corpus rebuild verified

The separate source extraction cloned the public transcript repository, checked out `be8ab89a890a833cbba2c892178f823fff178c65`, ingested 303 episodes with zero skipped episodes, and independently rebuilt its local lexical/Chroma index. The refresh process exited 0. Its 23,702 chunks have SHA256 `1a0e5a879be61490559f1082526540826da62c4518e672bcdfb88271fc7284b7`, matching the original manifest, along with revision, chunk settings and embedder.

All 83 backend tests then passed against that independently rebuilt index in 8.06 seconds, using the separate locked-dependency installation and isolated test database. This supersedes the earlier root-index reuse limitation for this test run. It still does not prove public-repository cloning, a full fresh-machine PostgreSQL/Ollama setup, or the camera-enabled video. The final real model essay/artifact job remains running; its API has completed two source-section audits.

## Latest essay and heading regression

The final strict-mode Llama essay completed and persisted: 1,188 words, one Markdown artifact, no automatic warnings, first text 25.3 seconds and total 458.8 seconds. Manual source/presentation findings are recorded in `evaluation/latest-essay-review.md`; a passing count/grounded flag does not certify editorial or factual quality. The HTML and Markdown follow-ups remain live.

A real missing Step 4 was caused by a generated application subheading at the same level as the canonical step. Step-body headings are now demoted below the step, preserving the hierarchy through cleanup. The regression and full 83-test backend suite passed (9.37 seconds). Replaying the actual retained Step 4 section through the fixed formatter also passed; `evaluation/heading-repair-probe.json` records input/output without changing saved messages or claiming new generation. The running API's essay predates this formatting fix, which is covered by these targeted checks.

## Completed conversation conversion fix

The model-rewrite run exited 1: the 1,188-word essay and a 386-word Markdown reply persisted, but HTML failed reference verification after 244.5 seconds and produced no artifact. Its original reports/text are preserved under `failed-model-rewrite-`. The evaluator now removes stale artifact files before writing outputs, preventing a prior HTML file from appearing to belong to a failed run.

Referential conversion now extracts complete saved paragraphs and application bullets from the original grounded answer without another retrieval/model request. Explicit new topics still use Pi and retrieval. All 89 backend tests passed after source-preserving conversion and chain handling (4.77 seconds). The first new test collection used pytest's reserved `request` parameter name; renaming it resolved collection, and all six conversion tests passed.

Real HTML and Markdown retries each persisted one 441-word artifact with the original citation identifiers and no warnings. Both client timings rounded to 0.0 seconds; server formatting took approximately 1 millisecond. First-text timing is null because no model token stream occurred. The real saved conversation includes six artifacts across original generation and retries; these have not been relabeled as a single successful fresh generation.

Chrome passed palette/mobile/isolation checks, then the saved-output check passed for all six actual artifacts: reload, native previews, exact code, clipboard copying and byte-identical downloads. Its initial failure selected the wrong artifact when titles matched; selecting chips in persisted order fixed the test. Saved-output Chrome rerun passed in 6.3 seconds. Cloud UI labels now distinguish missing keys from configured keys, without implying a funded/working account; production build passed.

Functional local artifact evaluation is complete within this scope. Editorial/grounding limitations in `latest-essay-review.md` remain, and no 90% accuracy pass is claimed. Public GitHub, camera-enabled YouTube, funded cloud generation and a fresh public-clone setup remain unverified external dependencies.

## Latest packaged-source checks

The latest reviewed source was extracted over the independent locked-dependency installation without copying runtime assets. Its independently rebuilt corpus remained in place. All 89 backend tests passed there in 3.39 seconds; its current Node artifact-security test and frontend production build passed. Bash syntax and Python compile checks also passed. The source-only archive and Git bundle are regenerated after these results; bundle verification and offline cloning are checked by `prepare-submission.sh`. This is not a public repository or full fresh-machine service-installation proof.

Startup port collision fixed: `start.sh` now selects the next free API/UI ports and prints their URLs. With ports 8000 and 8001 occupied, the real startup chose backend 8002 and frontend 5173. Backend `/health`, frontend `/`, and frontend `/api/health` all returned HTTP 200. Bash syntax passed; existing listeners were left running.
