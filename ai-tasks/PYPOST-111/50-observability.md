# PYPOST-111: Observability

## Logging

Debug events (module `pypost.ui.widgets.paste_json_worker` and `code_editor`):

- `paste_json_worker_run_started` / `paste_json_worker_run_completed` — background parse outcome
- `code_editor_async_paste_started` — immediate large paste insert
- `code_editor_async_paste_applied` — formatted text replaced inserted region
- `code_editor_async_paste_skipped` — stale generation, invalid JSON, or user edited region

## Metrics

No new metrics. Paste volume is user-driven and infrequent relative to HTTP traffic.

## User-visible behaviour

Large JSON-like pastes appear instantly as clipboard text, then reformat in place when parsing
succeeds. No progress indicator or error dialog on failure (raw text kept).
