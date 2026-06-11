# PYPOST-409: Dev Documentation

## Changes Made

### Updated: `doc/dev/request_execution.md`

- Added paragraph under **Error handling** documenting that post-script failures use
  `execution_error` with `ErrorCategory.SCRIPT` and `detail` (PYPOST-409).
- Notes that `RequestWorker` and `MCPServerImpl` read script errors from `execution_error`.

## Validation

- [x] `ExecutionResult` field list in docs matches `pypost/core/request_service.py`
- [x] Error handling section consistent with PYPOST-400 structured error model
- [x] Test names in observability artifact align with `tests/test_request_service.py`

## Related

- PYPOST-400 introduced `execution_error`; this ticket completes TD-1 removal of legacy
  `script_error` field.
