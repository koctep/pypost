# PYPOST-412: Dev Docs

## Updates

| File | Change |
|------|--------|
| `doc/dev/request_execution.md` | Added worker signal scope: `finished` vs `error` |

## Content added

- `RequestWorker.error` is emitted only for unexpected exceptions wrapped as
  `ErrorCategory.UNKNOWN`.
- Handled execution failures (`ExecutionResult.execution_error`) use `finished` with
  synthetic error responses from `RequestService`.

## Verification

Documentation aligns with `RequestWorker.run()` and `tests/test_worker.py`.
