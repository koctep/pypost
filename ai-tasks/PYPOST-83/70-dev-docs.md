# Developer Documentation — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Author:** Team Lead
**Date:** 2026-03-25

---

## 1. What Changed and Why

### Problem

`RequestService._execute_http_with_retry` called `HTTPClient.send_request` with all
arguments passed positionally:

```python
# Before
response = self.http_client.send_request(
    request, variables, stream_callback, stop_flag, headers_callback
)
```

Three unit tests in `tests/test_request_service.py` verified argument forwarding by
reading from the mock's raw positional-argument tuple:

```python
call_kwargs[0][1]  # variables
call_kwargs[0][2]  # stream_callback
call_kwargs[0][4]  # headers_callback
```

Both patterns are fragile: adding or reordering any parameter of `send_request` would
silently pass the wrong value at runtime and cause the test assertions to compare the
wrong value or raise `IndexError`.

### Fix

`request_service.py` now passes the four optional parameters as keyword arguments:

```python
# After
response = self.http_client.send_request(
    request,
    variables=variables,
    stream_callback=stream_callback,
    stop_flag=stop_flag,
    headers_callback=headers_callback,
)
```

The three test assertions now use `call_args.kwargs` (name-based dict):

```python
call_kwargs.kwargs["variables"]
call_kwargs.kwargs["stream_callback"]
call_kwargs.kwargs["headers_callback"]
```

---

## 2. Files Modified

| File | Lines changed | Nature |
|---|---|---|
| `pypost/core/request_service.py` | 129–135 | Positional → keyword args at `send_request` call site |
| `tests/test_request_service.py` | 36, 44, 52 | `call_args[0][N]` → `call_args.kwargs["name"]` |

No other files were modified. No behaviour change at runtime.

---

## 3. How to Verify

```bash
pytest tests/test_request_service.py -v
```

Expected: 23 passed, 0 failed, 0 errors.

```bash
pytest --cov=pypost --cov-fail-under=50
```

Expected: coverage at or above 50 % threshold.

---

## 4. Guidance for Future Maintainers

### Adding a new parameter to `HTTPClient.send_request`

1. Add the new parameter to `HTTPClient.send_request` with a default value (optional
   parameters keep backward compatibility).
2. Update the call site in `request_service.py` with a new `name=value` keyword argument
   line.
3. If the new parameter needs test coverage, add a new test method that follows the same
   `call_kwargs.kwargs["name"]` assertion pattern — do **not** use `call_args[0][N]`.

### Why `call_args.kwargs` and not `call_args[1]`

Both access the same underlying dict (`call_args[1]` is the legacy tuple-index form).
`call_args.kwargs` is the named-attribute form introduced in Python 3.8 and is more
readable and explicit. Use `call_args.kwargs` consistently.

---

## 5. Related Tasks

| Task | Relationship |
|---|---|
| PYPOST-52 | Tech-debt review that identified this issue and raised PYPOST-83 |
| PYPOST-43–51 | Refactoring cycle during which the positional call site was introduced |
