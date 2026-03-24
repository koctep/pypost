# PYPOST-401: Code Cleanup

## Summary

Implementation is complete. The following cleanup actions were performed during the implementation pass.

## Cleanup Actions

### `pypost/core/worker.py`

- Removed the `self._is_stopped = False` reset line inside `run()` (was the root cause of RC-1/RC-2).
- Removed blank line inconsistency in `run()` body — spacing between inner closures is now uniform.
- No dead code introduced; no commented-out code left behind.

### `pypost/ui/presenters/tabs_presenter.py`

- Replaced the truthy check `if sender_tab.worker and ...` with explicit `is not None` checks for clarity and correctness.
- Stale reference cleanup block is placed immediately before the active-worker guard so the control flow is sequential and readable.
- No temporary variables or extraneous comments introduced.

### `tests/test_worker_race.py`

- Helper functions `_make_worker()` and `_ok_result()` are module-level, reused across all three test methods.
- `capture_stop_flag` side-effect accepts `*args, **kwargs` to match `service.execute`'s calling convention.
- `QApplication` instance is obtained via `instance() or QApplication([])` — consistent with the existing test suite pattern.
- No unused imports.

## Standards Check

| Rule | Status |
|---|---|
| Line length ≤ 100 chars | Verified — no line exceeds 100 characters |
| LF line endings | Verified |
| No trailing whitespace | Verified |
| Single final newline | Verified |
| English only | Verified |
| PEP 8 compliance | Verified |

## Test Results

```
6 passed in tests/test_worker.py + tests/test_worker_race.py
146 passed across full suite (4 pre-existing failures unrelated to this task)
```
