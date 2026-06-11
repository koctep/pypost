# PYPOST-413: Observability

## Logging

| Location | Level | Event |
|----------|-------|-------|
| `request_service._execute_http_with_retry` | `DEBUG` | `retry_cancelled_during_backoff` (unchanged) |
| `worker.run` | `DEBUG` | `worker_run_cancelled` (new) |
| `tabs_presenter._on_request_error` | `INFO` | `request_cancelled category=cancelled` |

## Metrics

| Metric | Change |
|--------|--------|
| `request_errors_total` | `CANCELLED` errors excluded from `track_request_error` |

User-initiated cancellation is not counted as a request execution error.

## Verification

- `tests/test_retry.py::test_stop_flag_cancels_retry` asserts `CANCELLED` category.
- No new Prometheus series required; `cancelled` label is reserved but not incremented
  for stop-flag paths.
