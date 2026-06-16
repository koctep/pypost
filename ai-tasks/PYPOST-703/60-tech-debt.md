# PYPOST-703: Technical Debt

## Non-blockers

- **Heuristic JSON key list** — Sensitive field names are regex-based; uncommon vendor keys may
  leak until PYPOST-706 expands masking heuristics.
- **Non-JSON bodies** — Plain-text responses only get hidden-value, Bearer, and query-token
  redaction; structured XML/form bodies are not parsed.
- **Truncation** — Very large bodies are not capped; consider size limits in a perf sprint.

No Jira follow-ups required for close.
