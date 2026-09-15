# Camera-enabled demo — 2 to 3 minutes

Record your screen with your webcam visible (OBS Studio, Loom or your preferred recorder). Close terminals containing secrets. Keep Ollama selected. Pre-generate the essay before recording because CPU generation can take several minutes; openly identify it as a saved locally generated result.

## Suggested sequence and narration

**0:00–0:25 — problem and user.** “Product teams need trustworthy expert advice and reusable briefs. This assistant searches Lenny's transcripts, shows sources and turns a conversation into documents inside the app.” Show the new-chat screen.

**0:25–1:05 — live local question.** Show Ollama / llama3.2:3b in the provider menu. Ask a question about activation or onboarding. Show progress, sources and streamed text. Open a timestamped citation and briefly connect a claim to its evidence. If generation is pending, continue explaining retrieval; do not imply a saved result was newly generated.

**1:05–1:35 — conversation and essay.** Reopen a saved local chat, show the follow-up and Ship 30 essay. Show hook, headings, bullets and citations. Explain the reusable writing rules and approximately 1,250-word target. Show any quality warning honestly.

**1:35–2:10 — artifacts.** Open the generated HTML brief beside chat. Switch preview/code; show Markdown too if time permits. Mention artifacts survive reload and HTML previews cannot run scripts or contact external services.

**2:10–2:40 — trade-off and handoff.** “The CPU-friendly 3B model keeps the demo local, but long answers are slower and citations still need factual review. The faster 1B model was too shallow. Cloud models are configurable, with no hidden cloud fallback. PostgreSQL stores chats and artifacts; the README explains setup, tests and failure recovery.”

Upload the finished 2–3 minute video to YouTube with evaluator-accessible visibility, and record its URL in `docs/submission-checklist.md`. The assignment asks for camera enabled, so a generated slideshow or screen-only recording does not satisfy it.
