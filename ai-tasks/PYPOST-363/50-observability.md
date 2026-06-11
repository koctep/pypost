# PYPOST-363: Observability

## Logging

No new log lines. `_on_search_text_changed` still emits:

- **DEBUG**: `response_search_typed query_len=%d matches=%d` — now fires after debounce on large
  documents (fewer log lines while typing).

## Metrics

Unchanged. `gui_response_search_actions_total{source="typed", ...}` still recorded when debounced
search runs, not on every intermediate keystroke on large docs.

## Operational Impact

- Large-document search metrics and debug logs reflect completed queries rather than partial
  keystrokes — more accurate signal of user intent.
