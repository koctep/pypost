# PYPOST-52: Tech Debt Analysis

## Overview

PYPOST-52 introduced 5 new files under `tests/` and updated 2 existing files
(Makefile, `test_request_manager_delete.py`). No production code was modified.
37 tests pass with 0 failures. The overall quality is good; the items below are
debt to address before or during the planned refactoring tasks (PYPOST-43–51).

---

## Findings

### HIGH — Fragile positional argument indexing in `test_request_service.py`

**Location**: `tests/test_request_service.py:38, 46, 54`

```python
# Current (fragile)
self.assertEqual({"k": "v"}, call_kwargs[0][1])   # variables
self.assertEqual(cb, call_kwargs[0][2])             # stream_callback
self.assertEqual(cb, call_kwargs[0][4])             # headers_callback
```

`call_args[0][N]` depends on the exact positional order of `send_request`'s
signature. If `RequestService.execute` or `HTTPClient.send_request` gains or
reorders a parameter during refactoring, these assertions will silently check
the wrong argument or raise `IndexError`.

**Recommended fix**: Use keyword-argument inspection:
```python
self.assertEqual({"k": "v"}, call_kwargs.kwargs.get("variables"))
```
or `call_args[1]` (kwargs dict) after verifying the call uses keyword passing.

---

### MEDIUM — `ScriptExecutor` patch targets class, not instance

**Location**: `tests/test_request_service.py:70–82`

```python
with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
    mock_executor.execute.return_value = ({"x": 1}, ["log"], None)
```

If `RequestService` calls `ScriptExecutor().execute(...)` (i.e., instantiates
the class then calls a method), `mock_executor.execute` is the class-level mock,
not the instance-level mock. The correct target would be
`mock_executor.return_value.execute.return_value`. The current tests pass
because `ScriptExecutor` may be called as a static/class method, but this
assumption should be made explicit with a comment or corrected.

---

### MEDIUM — Private attribute mutation in reload test

**Location**: `tests/test_request_manager.py:88`

```python
self.storage._collections = [col]
self.manager.reload_collections()
```

Directly mutating `_collections` (a private attribute) couples the test to the
`FakeStorageManager` implementation. If the attribute is renamed or the fake is
updated, the test will break silently (no attribute error, just wrong behaviour).

**Recommended fix**: Initialise the manager with the desired collections from
the start, or add a `set_collections()` helper to `FakeStorageManager`.

---

### LOW — `FakeStorageManager.saved_collections` stores names, not objects

**Location**: `tests/helpers.py:11`

```python
def save_collection(self, collection):
    self.saved_collections.append(collection.name)
```

Recording only the name means tests cannot assert on the full collection state
(e.g. that the requests list was serialised correctly). This is acceptable for
current tests but will become a gap when save-path tests are added in
PYPOST-43–51.

**Recommended fix** (deferred): Add `self.saved_collection_objects.append(collection)`
alongside the existing name list.

---

### LOW — `iter_content` mock returns strings, not bytes

**Location**: `tests/test_http_client.py:13`

```python
resp.iter_content.return_value = iter(chunks or ["body"])
```

The real `requests.Response.iter_content()` yields `bytes`. `HTTPClient` likely
calls `.decode()` on each chunk; the mock bypasses this code path. Tests pass
because the decode never executes against a mock, but the implicit contract is
wrong.

**Recommended fix**: Use `b"body"` / `b"chunk1"` etc. in `_make_response`.

---

### LOW — No `--cov-fail-under` threshold

**Location**: `Makefile` / `pytest.ini`

`make test-cov` generates a coverage report but does not enforce a minimum
percentage. A refactoring regression that deletes coverage could go unnoticed
in CI (when CI is added).

**Recommended action**: After running the baseline `make test-cov`, agree on a
floor (e.g. 70%) and add `--cov-fail-under=70` to the `test-cov` target.

---

### LOW — No CI integration

The `pytest.ini` and `make test-cov` improvements are local-only. No pipeline
runs tests on every push or PR.

**Recommended action**: Add a GitHub Actions workflow (`.github/workflows/test.yml`)
as a follow-up ticket. This is out of scope for PYPOST-52 but should be tracked.

---

### INFO — `helpers.py` lacks module-level docstring

`tests/helpers.py` has no module docstring explaining its purpose. Acceptable
for now given the small team, but worth adding when the file grows.

---

## Summary Table

| # | Severity | File | Description |
|---|---|---|---|
| 1 | HIGH | `test_request_service.py` | Positional `call_args` indexing is fragile |
| 2 | MEDIUM | `test_request_service.py` | `ScriptExecutor` patched at class level, not instance |
| 3 | MEDIUM | `test_request_manager.py` | Private `_collections` mutated in reload test |
| 4 | LOW | `tests/helpers.py` | `saved_collections` stores names only, not full objects |
| 5 | LOW | `test_http_client.py` | `iter_content` mock uses strings instead of bytes |
| 6 | LOW | `Makefile` | No `--cov-fail-under` threshold enforced |
| 7 | LOW | (infra) | No CI pipeline for automated test runs |
| 8 | INFO | `tests/helpers.py` | Missing module-level docstring |

---

## Verdict

No blocking issues. Items 1 and 2 carry the most risk for the upcoming
refactoring (PYPOST-43–51) because they may mask regressions introduced by
signature changes. These should be fixed before or during the first refactoring
ticket. Items 3–8 can be addressed opportunistically.
