# PYPOST-412: Observability

## Summary

No observability changes. Removing dead code does not alter log or metric emission.

## Before / after

| Event | Before | After |
|-------|--------|-------|
| Handled `ExecutionError` in `execute()` | Logged in `RequestService`; worker branch never ran | Same — `RequestService` only |
| Unexpected worker `Exception` | `logger.error` + `error.emit(UNKNOWN)` | Unchanged |
| Retry attempts | `retry_attempt` signal + service logs | Unchanged |

## Decision

No new logs or metrics required. Dead `logger.error("RequestWorker failed ...")` in the
removed branch was unreachable and duplicated `RequestService` logging.
