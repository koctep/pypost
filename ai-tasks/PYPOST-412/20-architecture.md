# PYPOST-412: Architecture — remove dead worker ExecutionError handler

## Current flow (before)

```
RequestWorker.run()
  try:
    result = RequestService.execute()   # never raises ExecutionError
    ...
    finished.emit(result.response)
  except ExecutionError:                # DEAD — unreachable
    error.emit(exc)
  except Exception:
    error.emit(UNKNOWN)
```

## Target flow

```
RequestWorker.run()
  try:
    result = RequestService.execute()     # returns ExecutionResult
    ... script_output from execution_error ...
    finished.emit(result.response)      # includes synthetic error responses
  except Exception:                      # only unexpected faults
    error.emit(UNKNOWN)
```

## Changes

| Component | Change |
|-----------|--------|
| `pypost/core/worker.py` | Delete `except ExecutionError` block (lines 131–133) |
| `tests/test_worker.py` | Remove mock-raise test; add `ExecutionResult` error → `finished` test |
| `doc/dev/request_execution.md` | Document worker `error` vs `finished` signal scope |

## Error handling contract (unchanged)

| Failure type | `RequestService` | `RequestWorker` signal |
|--------------|------------------|------------------------|
| HTTP/MCP/template (handled) | `ExecutionResult` + `execution_error` | `finished` |
| Post-script failure | `execution_error` on result | `finished` + `script_output` |
| Unexpected bug in worker | `Exception` | `error` (UNKNOWN) |
| Cancellation during retry | Caught in `execute()` → result | `finished` |

## Backward compatibility

- `error` signal type unchanged (`ExecutionError` or legacy `str` for cancellation).
- Public `RequestWorker` API unchanged.
- UI `_on_request_error` still handles unexpected worker faults only.

## Tests

| Test | Asserts |
|------|---------|
| `test_worker_emits_finished_on_execution_result_error` | `execution_error` set → `finished`, not `error` |
| `test_worker_wraps_unexpected_exception_as_execution_error_unknown` | Unchanged |
| `test_worker_emits_finished_on_success` | Unchanged |
