# PYPOST-403 Architecture — [HP] Fix failing tests in CI

**Author**: senior_engineer
**Date**: 2026-03-25
**Status**: Complete

---

## 1. Overview

Five failing tests are caused by two independent regressions. Each regression has a
production-side fix and a test-side fix. A housekeeping task (crash dump removal) is
also included. All changes are surgical; no existing passing tests or public APIs are
broken.

---

## 2. Fix A — SSE Probe Tests (`AttributeError` × 3)

### 2.1 Problem

`HTTPClient.__init__` stores `template_service` as `self._template_service` without
falling back to a default instance:

```python
# pypost/core/http_client.py:24
self._template_service = template_service   # may be None
```

`send_request` (line 150) and `_prepare_request_kwargs` (lines 31–45) call
`self._template_service.render_string(...)` unconditionally. When the three SSE probe
tests construct `HTTPClient()` with no arguments, `self._template_service` is `None`
and every call crashes with `AttributeError: 'NoneType' object has no attribute
'render_string'`.

### 2.2 Production-side fix — `pypost/core/http_client.py`

In `__init__`, replace the bare assignment with a default-construction guard:

```python
# Before
self._template_service = template_service

# After
self._template_service = template_service if template_service is not None \
    else TemplateService()
```

`TemplateService` is already imported at the top of the module (line 9), so no new
import is needed. The existing debug log is retained when the caller provides an
explicit instance.

**Contract preserved**: callers that already inject `TemplateService()` are unaffected
(the injected instance continues to be used). The parameter remains `Optional`.

### 2.3 Test-side fix — `tests/test_http_client_sse_probe.py`

Mirror the pattern from `tests/test_http_client.py` (line 22). In `setUp`, import and
inject a real `TemplateService()`:

```python
from pypost.core.template_service import TemplateService

class HTTPClientSSEProbeTests(unittest.TestCase):
    def setUp(self):
        self.metrics_patcher = patch(
            "pypost.core.http_client.MetricsManager",
            return_value=MagicMock(),
        )
        self.metrics_patcher.start()
        self.client = HTTPClient(template_service=TemplateService())  # add this
```

Each of the three test methods currently creates its own `HTTPClient()` inline. Those
instantiations must be replaced with `self.client`:

| Test method | Change |
|---|---|
| `test_auto_detects_sse_and_handles_read_timeout` | Replace `client = HTTPClient()` → `client = self.client` |
| `test_auto_detects_sse_by_url_and_content_type` | Replace `client = HTTPClient()` → `client = self.client` |
| `test_handles_non_200_sse_response` | Replace `client = HTTPClient()` → `client = self.client` |

Both the production guard (2.2) and the test injection (2.3) are applied. The
production guard is the permanent defensive measure; the test injection makes the test
intent explicit and independent of the guard.

---

## 3. Fix B — History Manager Tests (`OSError` × 2)

### 3.1 Problem

`HistoryManager._save_async()` spawns a **daemon thread** that writes `history.json`.
The thread reference is not retained after `t.start()` (line 108), so there is no way
to join it. When `test_append_single_entry` and `test_get_entries_newest_first` exit
the `tempfile.TemporaryDirectory()` context, `rmtree` races against the still-running
thread, which crashes with `OSError: [Errno 39] Directory not empty`.

### 3.2 Production-side fix — `pypost/core/history_manager.py`

**Step 1 — store the thread reference.**

Introduce `self._save_thread: threading.Thread | None = None` in `__init__` (after the
existing `_save_pending` attribute). Update `_save_async` to assign the thread to this
attribute before starting it:

```python
self._save_thread = t = threading.Thread(target=_run, daemon=True)
t.start()
```

**Step 2 — add a `flush()` method.**

```python
def flush(self) -> None:
    """Block until any in-progress async save has completed.

    Safe to call even if no save has been triggered. Intended for tests
    and teardown code that must synchronize before the storage path is
    cleaned up.
    """
    with self._save_lock:
        thread = self._save_thread
    if thread is not None:
        thread.join()
```

The method reads `_save_thread` under `_save_lock` and then joins outside the lock to
avoid a deadlock (the `_run` inner function also acquires `_save_lock` at the end of
each loop iteration).

`flush()` is idempotent: calling it when no save is in flight (thread is `None` or
already finished) is a no-op. The existing `_save_running` / `_save_pending` debounce
logic is untouched.

**`_manager_at` helper** in `test_history_manager.py` bypasses `__init__` using
`__new__`, so it must also be updated to initialise `_save_thread = None` alongside the
existing attribute assignments (line 149–153).

### 3.3 Test-side fix — `tests/test_history_manager.py`

Add `hm.flush()` in `test_append_single_entry` and `test_get_entries_newest_first`
immediately before the `TemporaryDirectory` context exits (i.e., as the last statement
inside the `with` block, after the assertions):

```python
def test_append_single_entry(self):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        hm = _manager_at(td)
        hm.append(_make_entry(url="https://a.com"))
        entries = hm.get_entries()
        self.assertEqual(1, len(entries))
        self.assertEqual("https://a.com", entries[0].url)
        hm.flush()   # wait for async save before temp dir cleanup

def test_get_entries_newest_first(self):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        hm = _manager_at(td)
        hm.append(_make_entry(url="https://first.com",  timestamp="2026-01-01T00:00:00Z"))
        hm.append(_make_entry(url="https://second.com", timestamp="2026-01-02T00:00:00Z"))
        hm.append(_make_entry(url="https://third.com",  timestamp="2026-01-03T00:00:00Z"))
        entries = hm.get_entries()
        self.assertEqual("https://third.com",  entries[0].url)
        self.assertEqual("https://second.com", entries[1].url)
        self.assertEqual("https://first.com",  entries[2].url)
        hm.flush()   # wait for async save before temp dir cleanup
```

No `time.sleep` is introduced, satisfying acceptance criterion 2.

---

## 4. Fix C — Housekeeping

### 4.1 Remove `core` crash dump

The `core` file in the repo root is an 86 MB ELF crash dump. It must be deleted from
the working tree:

```
rm core
```

### 4.2 Update `.gitignore`

Append the following entry so that future crash dumps are automatically excluded:

```gitignore
# ELF core dumps
core
core.*
```

---

## 5. File Change Summary

| File | Type | Change description |
|------|------|--------------------|
| `pypost/core/http_client.py` | Prod | Default-construct `TemplateService()` in `__init__` when arg is `None` |
| `pypost/core/history_manager.py` | Prod | Store `_save_thread`; add `flush()` method |
| `tests/test_http_client_sse_probe.py` | Test | Import `TemplateService`; inject in `setUp`; replace inline `HTTPClient()` with `self.client` |
| `tests/test_history_manager.py` | Test | Add `hm.flush()` to `test_append_single_entry` and `test_get_entries_newest_first`; init `_save_thread = None` in `_manager_at` |
| `.gitignore` | Housekeeping | Add `core` / `core.*` patterns |
| `core` (repo root) | Housekeeping | Delete file |

---

## 6. Acceptance Criteria Mapping

| AC | How satisfied |
|----|--------------|
| 1. `pytest tests/` exits 0 failed, 191 passed | All 5 failures addressed by the fixes above |
| 2. No unexplained `time.sleep` in tests | `flush()` replaces sleep; no new `sleep` calls |
| 3. `flush()` must not break existing passing tests | Existing tests do not call `flush()`; it is additive |
| 4. `HTTPClient` continues to accept optional `template_service` | Signature unchanged; default guard is internal |
| 5. `core` dump removed and ignored | Fix C covers deletion and `.gitignore` update |

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `flush()` deadlocks on `_save_lock` | Low | Read thread ref under lock, join outside lock |
| Other tests in `test_history_manager.py` break | Very low | `flush()` is additive; existing tests unaffected |
| Default `TemplateService()` construction in `HTTPClient` fails | Very low | `TemplateService` has no external dependencies |
| `test_append_enforces_cap` (501 appends) races | Low | Each append replaces previous thread; `flush()` joins final thread; already passing without sleep |
