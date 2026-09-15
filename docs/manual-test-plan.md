# Manual UI and factual evaluation

Use real API mode, PostgreSQL and Ollama / llama3.2:3b. Record hardware, corpus manifest, model, time to first text and final reply. Automated pass counts do not establish answer accuracy.

## Critical UI checklist

- Start with `./start.sh`; load port 5173 and confirm local provider/model.
- New chat: ask “How should an early-stage team improve activation?” Check progress, numbered claims and timestamped source links.
- Follow-up: ask “How would I apply that to a B2B product?” Check topic continuity.
- Start a second chat on pricing; verify it does not include the first chat's history. Switch back and reload.
- Request “Draft a Ship 30 for 30 essay on improving user activation.” Count 1,100–1,400 words, inspect hook, consistent headings, bullets, bold, takeaway and factual citations. Record any visible length warning.
- Request “Turn that into a Markdown document.” Check automatic viewer, code/preview, copy/download, close/reopen and recovery after browser reload.
- Request “Make an HTML one-pager explaining first-user experience and retention.” Check styled adjacent preview and downloaded complete HTML. Inspect browser network: preview must not make external requests.
- Stop a reply. Check send becomes available and cancelled partial text is not saved as a completed answer. Repeat by selecting another session while generating.
- Delete a session; verify history and artifacts are unavailable after reload.
- With no cloud keys, check disabled options. With your own funded credentials, intentionally select cloud and verify generation plus source links. Do not record credentials or billing pages.
- Stop Ollama and ask again. Check understandable error and saved question. Restore it. Test primary failure with explicitly configured local fallback.
- Stop PostgreSQL and refresh sessions. Check readable database error and degraded health. Restart PostgreSQL.
- On a test copy, move the local verifier weights aside and restart. Check `/health` reports `evidence_available=false`; requested content must be flagged and withheld from artifacts. Restore weights with `scripts/setup-evidence.py` and restart.
- With the submitted default `ALLOW_GENERAL_KNOWLEDGE=false`, test an off-topic question such as tomorrow's weather. It must refuse to invent a transcript-backed answer. If testing the optional general-knowledge mode, explicitly enable it and verify unsourced replies carry a visible warning and no citations. This optional mode is not the assignment demo configuration.
- Ask the same kind of narrow/off-topic question as a content-generation request ("Draft a Ship 30 for 30 essay on tomorrow's weather"). This must still be refused outright, since essay/artifact skills require transcript-grounded claims.

## Responsive and accessibility review

At 390px, 768px, 1024px and 1440px, check sidebar/drawer, long replies, composer, source cards and artifact overlay/pane. Use keyboard only: new chat, provider options, composer, artifact preview/code, close, copy/download. Check visible focus, readable warnings, 200% zoom and a screen reader. Record failures; do not assert untested accessibility conformance.

## Ten-question evidence set

Run the documented set against a running local instance:

```bash
EVALUATION_API_URL=http://127.0.0.1:5173/api .venv/bin/python scripts/evaluate-factual.py
```

The runner uses Ollama explicitly, checks persisted replies, and writes answers plus the retrieved context to `docs/evaluation/factual-report.json`. Question 9 reuses question 2's chat. Generation is sequential to avoid competing CPU requests. Its completion message proves request/persistence checks, not factual accuracy; annotate each claim against the captured excerpts before reporting a supported-claim percentage.

1. How does Rahul Vohra measure product-market fit?
2. What is an activation aha moment, and how did Hila Qu approach it at GitLab?
3. Why does Merci Grace recommend designing onboarding early?
4. Why does Dan Hockenmaier focus on the first user experience for retention?
5. What growth gaps did Crystal Widjaja describe at Gojek?
6. How should a B2B SaaS team approach pricing?
7. How do growth loops differ from a funnel?
8. How should a team choose a north-star metric?
9. Follow-up to question 2: How would I apply that to my team?
10. What is tomorrow's exact weather forecast? (Expected in the submitted configuration: a refusal because the transcripts cannot supply a live forecast.)

For each answer, map every substantive claim to a retrieved excerpt. Score supported, unsupported, wrong citation or unclear. Inspect the actual excerpt, not only the source title. Report supported claims / all factual claims, refusal correctness and citation-link correctness. Questions without corpus support must get a refusal in the submitted default configuration rather than a fabricated transcript-grounded answer.
