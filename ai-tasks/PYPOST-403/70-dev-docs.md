# PYPOST-403 Developer Docs — [HP] Fix failing tests in CI

**Author**: team_lead
**Date**: 2026-03-25
**Status**: Complete

---

## 1. What Changed and Why

PYPOST-403 fixed five CI test failures caused by two independent regressions:

| Regression | Root cause | Tests affected |
|------------|-----------|----------------|
| A — SSE probe `AttributeError` | `HTTPClient` stored `None` for `_template_service` when no argument was passed, then crashed on first method call | 3 tests in `test_http_client_sse_probe.py` |
| B — History manager `OSError` | `HistoryManager._save_async` discarded the thread reference, making it impossible to join before temp-dir cleanup | 2 tests in `test_history_manager.py` |

A housekeeping task (removing an 86 MB `core` ELF crash dump and updating `.gitignore`)
was included in the same ticket.

---

## 2. `pypost/core/http_client.py`

### Change: default `TemplateService` construction

**Location**: `HTTPClient.__init__` (~line 24)

```python
# Before
self._template_service = template_service

# After
self._template_service = template_service if template_service is not None \
    else TemplateService()
```

**Contract**: `HTTPClient()` can now be constructed with no arguments. `_template_service`
is always a valid `TemplateService` instance after `__init__` completes. Callers that
already inject an explicit instance are unaffected.

**Logging**: the constructor emits a `DEBUG` log line for both paths:
- `HTTPClient: using injected TemplateService id=<id>` (injected)
- `HTTPClient: using default TemplateService` (default-constructed)

---

## 3. `pypost/core/history_manager.py`

### Change A: store save-thread reference

**Location**: `HistoryManager.__init__` and `_save_async`

A new instance attribute `_save_thread: threading.Thread | None = None` is added in
`__init__`. In `_save_async`, the thread is assigned to this attribute before being
started:

```python
self._save_thread = t = threading.Thread(target=_run, daemon=True)
t.start()
```

This allows `flush()` (see below) to join the thread.

### Change B: `flush()` method

```python
def flush(self) -> None:
    """Block until any in-progress async save has completed."""
```

**Behaviour**:
- Reads `_save_thread` under `_save_lock` (snapshot, to avoid holding the lock during
  the join).
- Calls `thread.join()` outside the lock. If the thread has already finished, `join()`
  returns immediately.
- Safe to call when no save has ever been triggered (`_save_thread is None` → no-op).
- Idempotent: calling it multiple times is safe.

**When to use `flush()`**: call it in test teardown or application shutdown code that
must ensure the history file is fully written before cleaning up the storage path.

**Log lines emitted** (both at `DEBUG` level):
```
history_manager_flush waiting thread_id=<id>
history_manager_flush complete
```

### Observability additions

| Event | Level | Format |
|-------|-------|--------|
| History cap enforced (entry dropped) | `WARNING` | `history_cap_enforced max=<N> oldest_entry_dropped=True` |
| Async save completed | `DEBUG` | `history_manager_saved count=<N> elapsed_ms=<ms>` |
| Async save failed | `DEBUG` | `history_manager_save_failed elapsed_ms=<ms> error=<exc>` |
| `flush()` waiting | `DEBUG` | `history_manager_flush waiting thread_id=<id>` |
| `flush()` complete | `DEBUG` | `history_manager_flush complete` |

---

## 4. Test Changes

### `tests/test_http_client_sse_probe.py`

- Added `from pypost.core.template_service import TemplateService` import.
- `setUp` now constructs `self.client = HTTPClient(template_service=TemplateService())`.
  All three test methods replaced their inline `client = HTTPClient()` with `self.client`.

**Why**: the production fix (default construction) makes the tests pass without injection,
but explicit injection in `setUp` makes the test intent clear and independent of the
production guard.

### `tests/test_history_manager.py`

- `_manager_at` helper (which uses `__new__` to bypass `__init__`) now initialises
  `hm._save_thread = None` alongside the other manually assigned attributes.
- `test_append_single_entry` and `test_get_entries_newest_first` call `hm.flush()` as the
  last statement inside the `with tempfile.TemporaryDirectory()` block, before the context
  manager triggers `rmtree`.

### `tests/test_http_client.py`

- `test_no_injection_sets_template_service_to_none` renamed to
  `test_no_injection_creates_default_template_service` and updated to assert
  `assertIsInstance(client._template_service, TemplateService)` instead of
  `assertIsNone(client._template_service)`.

---

## 5. `.gitignore`

Two patterns were appended to prevent future ELF crash dumps from being committed:

```gitignore
# ELF core dumps
core
core.*
```

---

## 6. Running the Tests

```bash
pytest tests/
# Expected: 191 passed
```

To run only the files touched by this ticket:

```bash
pytest tests/test_http_client.py tests/test_http_client_sse_probe.py tests/test_history_manager.py -v
# Expected: 24 passed
```
