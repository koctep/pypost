# PYPOST-413: Dev Docs

## Updates

| File | Change |
|------|--------|
| `doc/dev/request_execution.md` | Cancellation section; worker `error` signal includes `CANCELLED` |

## Content added

- `ErrorCategory.CANCELLED` for user-initiated stop via `stop_flag`.
- Worker routes `CANCELLED` `ExecutionResult` to `error` signal.
- UI detects cancellation by category, not `detail` substring.

## Verification

Documentation aligns with `RequestWorker.run()`, `RequestService._execute_http_with_retry`,
and `tests/test_tabs_presenter.py`.
