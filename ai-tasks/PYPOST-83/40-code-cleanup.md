# Code Cleanup — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Author:** Junior Engineer
**Date:** 2026-03-25
**Status:** Complete

---

## 1. Changes Made

### `pypost/core/request_service.py` (lines 129–135)

Converted positional arguments to keyword arguments at the `send_request` call site.
Each of the four parameters (`variables`, `stream_callback`, `stop_flag`,
`headers_callback`) is now passed by name. `request` remains positional as the primary
object whose position is stable.

### `tests/test_request_service.py` (lines 36, 44, 52)

Replaced three fragile `call_args[0][N]` positional-index assertions with
`call_args.kwargs["name"]` keyword-dict lookups:

| Test method | Before | After |
|---|---|---|
| `test_execute_passes_variables_to_http_client` | `call_kwargs[0][1]` | `call_kwargs.kwargs["variables"]` |
| `test_execute_stream_callback_forwarded_to_http_client` | `call_kwargs[0][2]` | `call_kwargs.kwargs["stream_callback"]` |
| `test_execute_headers_callback_forwarded_to_http_client` | `call_kwargs[0][4]` | `call_kwargs.kwargs["headers_callback"]` |

---

## 2. Test Results

```
23 passed in 0.96s
```

All tests in `tests/test_request_service.py` pass with no failures or warnings.

---

## 3. Code Quality Notes

- No trailing whitespace introduced.
- Line length remains within the 100-character limit.
- No new imports or dependencies added.
- Scope strictly limited to the two files identified in the architecture document.
- No behaviour change at runtime; pure refactor.
