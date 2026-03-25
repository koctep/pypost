# PYPOST-84: Developer Documentation

## Overview

This task clarified the mock contract for `ScriptExecutor` in the request-service test suite.
It is a comment-only change with no runtime impact.

---

## Background: Why `mock_executor.execute`, not `mock_executor.return_value.execute`

`ScriptExecutor.execute` is declared as a `@staticmethod` in
`pypost/core/script_executor.py:49`:

```python
@staticmethod
def execute(script, request, response, variables):
    ...
```

`RequestService` calls it at the class level — no instance is created:

```python
# pypost/core/request_service.py:281
ScriptExecutor.execute(...)
```

When `unittest.mock.patch` replaces `ScriptExecutor` with a `MagicMock`, the mock mirrors
this class-level API:

| Production call style | Correct mock target |
|---|---|
| `ScriptExecutor.execute(...)` (`@staticmethod`) | `mock_executor.execute.return_value` |
| `ScriptExecutor().execute(...)` (instance method) | `mock_executor.return_value.execute.return_value` |

Using `mock_executor.execute` is therefore **correct for the current design**.

---

## What Was Changed

Four identical 3-line comments were added to `tests/test_request_service.py` — one
immediately above each `mock_executor.execute.return_value = (...)` assignment:

```python
# ScriptExecutor.execute is a @staticmethod, so mock_executor.execute (not
# mock_executor.return_value.execute) is the correct target. If execute is ever
# converted to an instance method, change this to:
#   mock_executor.return_value.execute.return_value = (...)
mock_executor.execute.return_value = (...)
```

### Affected locations

| Test method | Approx. line |
|---|---|
| `TestRequestServicePostScript.test_execute_post_script_populates_logs_and_variables` | 64 |
| `TestRequestServicePostScript.test_execute_post_script_error_sets_script_error_field` | 76 |
| `TestRequestServiceErrorHandling.test_script_error_populates_execution_error_script_category` | 225 |
| `TestRequestServiceErrorHandling.test_script_error_tracks_metrics` | 249 |

---

## If `ScriptExecutor.execute` Is Ever Promoted to an Instance Method

1. Grep for `return_value.execute` in `tests/test_request_service.py` — this will surface
   all four sites.
2. Update each site from:
   ```python
   mock_executor.execute.return_value = (...)
   ```
   to:
   ```python
   mock_executor.return_value.execute.return_value = (...)
   ```
3. Also update `pypost/core/request_service.py` to call `ScriptExecutor().execute(...)`.
4. Run `make test` to confirm 0 failures.

---

## Files Modified

| File | Change |
|---|---|
| `tests/test_request_service.py` | Comments added at four patch sites |

No production files were modified.
