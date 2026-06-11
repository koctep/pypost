# PYPOST-409: Observability

## Impact

No observability changes. This refactor removes a redundant field; error paths unchanged.

## Metrics

- `request_errors_total{category="script"}` — still incremented in `RequestService.execute()`
  when post-script fails (`track_request_error(ErrorCategory.SCRIPT)`).

## Logging

| Location | Level | When |
|----------|-------|------|
| `tabs_presenter._on_script_output` | WARNING | Script error string received via worker signal |
| `request_service` (script path) | — | No new log lines; metrics path unchanged |

## Worker signal

`RequestWorker.script_output` still emits `(logs, error_message)` where `error_message` is
now sourced from `execution_error.detail` instead of `result.script_error`. UI and log format
unchanged.

## Verification

- `test_script_error_tracks_metrics` — confirms metric still fired after field removal.
- `test_execute_post_script_error_sets_execution_error` — confirms structured error populated.
