# PYPOST-420 — Code Cleanup

> Junior Engineer: junior_engineer
> Date: 2026-03-26

---

## Files Modified

| File | Change type |
|------|-------------|
| `pypost/core/alert_manager.py` | Handler guard, `close()`, `__enter__`/`__exit__` |
| `tests/test_alert_manager.py` | New `TestAlertManagerAccumulation` class |

---

## Changes Applied

### `pypost/core/alert_manager.py`

- Added handler guard loop in `__init__` before `addHandler()`: iterates
  `self._logger.handlers`, closes and removes each stale handler, then adds the fresh one.
- Stored `self._handler` as an owned reference to the handler created by this instance.
- Added `close()`: independently tries `self._handler.close()` and
  `self._logger.removeHandler(self._handler)`; all exceptions swallowed.
- Added `__enter__` / `__exit__` for context-manager support; `__exit__` delegates to
  `close()`.

### `tests/test_alert_manager.py`

- Added `import gc` at top.
- Added `TestAlertManagerAccumulation` with two test methods:
  - `test_no_accumulation_via_close`: creates 6 managers serially with explicit `close()`,
    verifies exactly 6 log lines.
  - `test_no_accumulation_via_gc_id_reuse`: uses `del` + `gc.collect()` to trigger CPython
    address reuse, verifies the handler guard prevents accumulation (6 lines, not more).

---

## Style / Standards Compliance

- Line length: all lines ≤ 100 characters.
- `# noqa: BLE001` retained on broad `except Exception` blocks (consistent with existing
  style in `_send_webhook`).
- No trailing whitespace; single final newline on each file.
- Type annotations preserved; `*_: object` on `__exit__` matches PEP 484 / mypy-clean
  pattern.
- No docstrings added to unchanged methods; `close()` has a one-line docstring per
  project convention.

---

## Test Results

```
17 passed in 0.71s
```

All pre-existing tests pass unchanged. Both new regression tests pass.
