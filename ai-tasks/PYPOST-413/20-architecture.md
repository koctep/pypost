# PYPOST-413: Architecture — type-safe cancellation

## Current flow (before)

```
stop_flag() == True
  → ExecutionError(category=NETWORK, message="Request cancelled", detail=...)
  → ExecutionResult → finished → synthetic status-0 response in panel
_on_request_error(ExecutionError):
  if "cancelled" in detail or "aborted" in detail → silent return  # imprecise
```

## Target flow

```
stop_flag() == True
  → ExecutionError(category=CANCELLED, message="Request cancelled", detail=...)
  → ExecutionResult (no request_errors_total increment)
  → RequestWorker.error.emit(exc)  # not finished
_on_request_error(ExecutionError):
  if error.category == CANCELLED → log + silent return
```

## Changes

| Component | Change |
|-----------|--------|
| `pypost/models/errors.py` | Add `CANCELLED = "cancelled"` |
| `pypost/core/request_service.py` | Stop-flag raises use `CANCELLED`; skip metrics for it |
| `pypost/core/worker.py` | Emit `error` when `execution_error.category == CANCELLED` |
| `pypost/ui/presenters/tabs_presenter.py` | Category check replaces detail substring match |

## Backward compatibility

- `str` cancellation payloads unchanged (legacy worker comment path).
- `request_errors_total` label set unchanged; `cancelled` is a new label value not emitted
  for user stops.

## Tests

| Test | Asserts |
|------|---------|
| `test_execution_error_cancelled_no_dialog` | `CANCELLED` category, no dialog |
| `test_worker_emits_error_on_cancelled_execution_result` | `error` signal, not `finished` |
| `test_stop_flag_cancels_retry` | `execution_error.category == CANCELLED` |
