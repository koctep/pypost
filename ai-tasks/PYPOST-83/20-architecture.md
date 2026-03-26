# Architecture — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Author:** Senior Engineer
**Date:** 2026-03-25
**Status:** Ready for Team Lead review

---

## 1. Overview

This is a pure refactor with no behaviour change. Two source files receive minimal,
targeted edits:

| File | Change |
|---|---|
| `pypost/core/request_service.py` | Switch positional args to keyword args at the `send_request` call site |
| `tests/test_request_service.py` | Replace three `call_args[0][N]` index assertions with `call_args.kwargs["name"]` |

No other files are touched.

---

## 2. Current State

### 2.1 Production call site — `request_service.py` lines 129–131

```python
response = self.http_client.send_request(
    request, variables, stream_callback, stop_flag, headers_callback
)
```

All five arguments are passed positionally. Any reordering of `send_request`'s
parameters will silently break callers.

### 2.2 Fragile test assertions — `test_request_service.py`

| Line | Current assertion | Positional index |
|---|---|---|
| 36 | `call_kwargs[0][1]` | `variables` at position 1 |
| 44 | `call_kwargs[0][2]` | `stream_callback` at position 2 |
| 52 | `call_kwargs[0][4]` | `headers_callback` at position 4 |

`call_args[0]` is the `args` tuple of the mock call. Numeric indexing is brittle:
inserting or reordering a parameter produces a wrong-value comparison or `IndexError`.

---

## 3. Target State

### 3.1 Production call site — keyword arguments

```python
response = self.http_client.send_request(
    request,
    variables=variables,
    stream_callback=stream_callback,
    stop_flag=stop_flag,
    headers_callback=headers_callback,
)
```

`request` stays positional (it is the primary object and its position is stable).
The remaining four parameters become keyword arguments, making the call site resilient
to parameter reordering.

### 3.2 Test assertions — `.kwargs` lookups

```python
# test_execute_passes_variables_to_http_client (line 36)
self.assertEqual({"k": "v"}, call_kwargs.kwargs["variables"])

# test_execute_stream_callback_forwarded_to_http_client (line 44)
self.assertEqual(cb, call_kwargs.kwargs["stream_callback"])

# test_execute_headers_callback_forwarded_to_http_client (line 52)
self.assertEqual(cb, call_kwargs.kwargs["headers_callback"])
```

`call_args.kwargs` is the keyword-argument dict recorded by `unittest.mock`. It is
name-based and immune to positional layout changes. This attribute is available in
Python 3.8+ (the project's minimum version).

---

## 4. Change Plan

### Step A — `pypost/core/request_service.py`

Replace lines 129–131:

**Before:**
```python
response = self.http_client.send_request(
    request, variables, stream_callback, stop_flag, headers_callback
)
```

**After:**
```python
response = self.http_client.send_request(
    request,
    variables=variables,
    stream_callback=stream_callback,
    stop_flag=stop_flag,
    headers_callback=headers_callback,
)
```

Diff size: 6 lines changed (3 removed, 6 inserted). All within the existing `try` block;
indentation and surrounding logic are untouched.

### Step B — `tests/test_request_service.py`

Three single-line replacements:

| Line | Before | After |
|---|---|---|
| 36 | `self.assertEqual({"k": "v"}, call_kwargs[0][1])` | `self.assertEqual({"k": "v"}, call_kwargs.kwargs["variables"])` |
| 44 | `self.assertEqual(cb, call_kwargs[0][2])` | `self.assertEqual(cb, call_kwargs.kwargs["stream_callback"])` |
| 52 | `self.assertEqual(cb, call_kwargs[0][4])` | `self.assertEqual(cb, call_kwargs.kwargs["headers_callback"])` |

No other lines in the test file change.

---

## 5. Correctness Reasoning

After Step A the mock records the call as:
```
args   = (request,)
kwargs = {"variables": ..., "stream_callback": ..., "stop_flag": ..., "headers_callback": ...}
```

After Step B the assertions read from `kwargs` by name, so they will find the expected
values. Steps A and B are co-dependent: both must land together or the tests will fail.

The runtime path through `send_request` is unchanged — Python resolves keyword arguments
to the same parameter slots as before, so no behaviour difference exists at runtime.

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Test regression | Low | Low | Both changes are applied together; `pytest` confirms green state |
| Accidental scope creep | Low | Low | Strict diff: only the 4 lines identified above |
| Python version incompatibility | None | — | `call_args.kwargs` exists since Python 3.8 |

---

## 7. Acceptance Criteria Mapping

| AC | How it is satisfied |
|---|---|
| AC-1: `call_args[0][N]` removed | Step B replaces all three occurrences |
| AC-2: `.kwargs["name"]` assertions present | Step B introduces them |
| AC-3: keyword args at call site | Step A introduces them |
| AC-4: `pytest tests/test_request_service.py` exits 0 | Verified after implementation |
| AC-5: no other test file modified | Only `tests/test_request_service.py` is touched |
