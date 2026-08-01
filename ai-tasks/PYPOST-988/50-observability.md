# PYPOST-988: Observability

## Logging

Structured log lines (module `environment_export` / widget orchestration):

| Event | Level | Fields |
| --- | --- | --- |
| `environment_export_payload_built` | INFO | `count`, `includes_hidden` |
| `environment_export_file_written` | INFO | `path` |
| `environment_export_no_selection` | WARNING | `scope` |
| `environment_export_failed` | WARNING | `reason` |
| `environment_export_completed` | INFO | `count`, `includes_hidden`, `path` |

## Tests

- `test_logs_completed_event` in `tests/test_environment_export_ui.py` asserts
  `environment_export_completed` via `caplog`.

## Metrics

No new metrics counters — export is a rare, user-initiated action; logging suffices
(same rationale as PYPOST-986 import).

## Worklog

tokens_used: 2000
role: execution
step: 6
step_name: Observability
