# PYPOST-989: Observability

## Logging

Structured log lines (module `collection_export` / export orchestration):

| Event | Level | Fields |
| --- | --- | --- |
| `collection_export_payload_built` | INFO | `collection_name`, `request_count` |
| `collection_export_file_written` | INFO | `path` |
| `collection_export_no_selection` | WARNING | — |
| `collection_export_failed` | WARNING | `reason` |
| `collection_export_completed` | INFO | `collection_name`, `request_count`, `path` |

## Tests

- `test_logs_completed_event` in `tests/test_collection_export_ui.py` asserts
  `collection_export_completed` via `caplog`.

## Metrics

No new metrics counters — export is a rare, user-initiated action; logging suffices
(same rationale as PYPOST-987 import and PYPOST-988 export).

## Worklog

tokens_used: 1500
role: execution
step: 6
step_name: Observability
