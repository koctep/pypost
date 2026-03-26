# Requirements — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Issue type:** Tech Debt
**Priority:** Medium
**Source:** ai-tasks/PYPOST-52/60-review.md
**Date:** 2026-03-25

---

## 1. Background

`tests/test_request_service.py` contains three test methods that assert arguments forwarded
from `RequestService.execute()` to `http_client.send_request()` by inspecting
`call_args[0][N]` — the raw positional-argument tuple at a numeric index:

| Test method | Line | Index checked | Argument expected |
|---|---|---|---|
| `test_execute_passes_variables_to_http_client` | 36 | `[0][1]` | `variables` |
| `test_execute_stream_callback_forwarded_to_http_client` | 44 | `[0][2]` | `stream_callback` |
| `test_execute_headers_callback_forwarded_to_http_client` | 52 | `[0][4]` | `headers_callback` |

The corresponding call site in `request_service.py` (line 129–131) passes all five arguments
positionally:

```python
response = self.http_client.send_request(
    request, variables, stream_callback, stop_flag, headers_callback
)
```

`http_client.HTTPClient.send_request` signature (lines 142–145):

```python
def send_request(self, request_data, variables=None,
                 stream_callback=None, stop_flag=None,
                 headers_callback=None) -> ResponseData:
```

### Problem

If any refactoring (e.g., inserting a new parameter, reordering existing ones) changes the
positional layout of `send_request`, the numeric-index assertions will silently compare the
wrong value or raise `IndexError`. This was flagged as a risk during the PYPOST-43–51
refactoring cycle.

---

## 2. Scope

This task is limited to two source files:

- `pypost/core/request_service.py` — production call site
- `tests/test_request_service.py` — three test assertions

No changes to `http_client.py`, `models/`, or any other file are in scope.

---

## 3. Functional Requirements

### FR-1 — Use keyword arguments at the call site

`request_service.py` line 129–131 **must** call `send_request` with keyword arguments for
every parameter after `request`:

```python
response = self.http_client.send_request(
    request,
    variables=variables,
    stream_callback=stream_callback,
    stop_flag=stop_flag,
    headers_callback=headers_callback,
)
```

The first positional argument (`request`) may remain positional as it is the primary object
and never changes position.

### FR-2 — Replace positional index assertions with `.kwargs` lookups

The three test assertions **must** use `call_args.kwargs` (or equivalently `call_args[1]`)
to look up arguments by name rather than by position:

| Test | Old assertion | New assertion |
|---|---|---|
| `test_execute_passes_variables_to_http_client` | `call_kwargs[0][1]` | `call_kwargs.kwargs["variables"]` |
| `test_execute_stream_callback_forwarded_to_http_client` | `call_kwargs[0][2]` | `call_kwargs.kwargs["stream_callback"]` |
| `test_execute_headers_callback_forwarded_to_http_client` | `call_kwargs[0][4]` | `call_kwargs.kwargs["headers_callback"]` |

### FR-3 — All existing tests must continue to pass

No currently-passing test may be broken by this change. The test suite must remain green
before and after the fix.

### FR-4 — No behaviour change

This is a refactor only. The runtime behaviour of `RequestService.execute()` must be
identical to before. No logic, error handling, retry behaviour, metrics, or history
recording may be altered.

---

## 4. Non-Functional Requirements

- **NFR-1 Minimal diff:** Only touch the lines identified above. Do not refactor surrounding
  code, add docstrings, or make unrelated cleanups.
- **NFR-2 Style:** Follow existing code style (line length ≤ 100 chars, LF endings, UTF-8).
- **NFR-3 Test coverage:** Coverage must not decrease (current threshold: 50 %).

---

## 5. Acceptance Criteria

1. `call_args[0][1]`, `call_args[0][2]`, `call_args[0][4]` no longer appear in
   `tests/test_request_service.py`.
2. The three affected assertions use `call_args.kwargs["variables"]`,
   `call_args.kwargs["stream_callback"]`, and `call_args.kwargs["headers_callback"]`
   respectively.
3. `request_service.py` passes `variables`, `stream_callback`, `stop_flag`, and
   `headers_callback` as keyword arguments to `send_request`.
4. `pytest tests/test_request_service.py` exits with code 0 with all tests passing.
5. No other test file is modified.
