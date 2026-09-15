# Qwen2.5:3b local pilot review

All three requests completed through Pi, FastAPI, retrieval, Ollama and PostgreSQL. Cloud fallback was disabled. The report stores actual answers, contexts and session provider/model metadata. This API used the citation-repair pipeline before its whitespace-only correction; the developer's general-knowledge option was enabled, but these three answers stayed on the retrieved-evidence path. The final Llama artifact run uses explicit strict mode.

| Question | Timing | Source review |
| --- | --- | --- |
| PMF measurement | 81.6 seconds; first text 43.3 | Gives the survey question and three choices but omits the 40% measurement benchmark. Citation 4 is the survey-method/baseline passage; the survey content is in passage 3. The classifier accepted the wrong reference. |
| Hila / activation | 105.6 seconds; first text 40.1 | Correctly retains two users/two features/14 days from passage 1, and its correlation-analysis recommendation is supported there. The explanation of reaching product value is consistent with passage 3. Suggestions should be read as applications, not experimentally proved outcomes. |
| Contextual follow-up | 122.6 seconds; first text 43.4 | Retains Hila/GitLab topic. Warm starts, templates and removing friction are supported by passage 1, but the audit leaves only numbered item 4. The introductory PLG reference does not provide actionable detail. The reply is incomplete. |

This is a functional configuration-switch demonstration, not a controlled model benchmark: the earlier Llama pilot used a preceding pipeline version. Qwen has not demonstrated a clear overall improvement, so llama3.2:3b remains the default. No 90% accuracy result is claimed. See `qwen-citation-score-probe.json` for the recorded classifier false positive/false negative.
