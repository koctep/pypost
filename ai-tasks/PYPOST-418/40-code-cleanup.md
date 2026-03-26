# PYPOST-418 — Code Cleanup

> Junior Engineer: 2026-03-26
> Jira: PYPOST-418

---

## Summary

All implementation changes were pure dependency-injection plumbing with no business
logic alterations. Code cleanup scope is minimal.

---

## Changes Made

### Files Modified

| File | Change |
|---|---|
| `pypost/models/settings.py` | Added `alert_log_path: Optional[str] = None` field |
| `pypost/main.py` | Imported `Path`, `AlertManager`; bootstrap `AlertManager`; passed to `MainWindow` |
| `pypost/ui/main_window.py` | Imported `AlertManager`; added `alert_manager` param; stored as `_alert_manager`; forwarded to `TabsPresenter` |
| `pypost/ui/presenters/tabs_presenter.py` | Imported `AlertManager`; added `alert_manager` param; stored as `_alert_manager`; forwarded to `RequestWorker` in `_handle_send_request` |
| `pypost/core/worker.py` | Imported `AlertManager`; added `alert_manager` param; forwarded to `RequestService` constructor |

### Test Files Modified

| File | Change |
|---|---|
| `tests/test_worker.py` | Added `TestRequestWorkerAlertManagerInjection` (2 tests) |
| `tests/test_tabs_presenter.py` | Added `TestTabsPresenterAlertManagerPropagation` (2 tests) |

---

## Cleanup Actions

- **Imports ordered**: New `AlertManager` imports placed after existing peer imports in
  each file, consistent with surrounding import grouping.
- **No dead code introduced**: All parameters default to `None`; no conditional stubs added.
- **Unused variable removed from test**: Removed dangling `original_init` assignment in
  `test_alert_manager_passed_to_worker` — the variable was set but never read.
- **Line length**: All added lines are within the 100-character limit.
- **Whitespace**: No trailing whitespace; files end with a single newline.

---

## Test Results

```
274 passed, 2 warnings in 2.44s
```

All pre-existing tests pass unchanged. 4 new tests added and passing.

---

## Notes

- `RequestService` already accepted `alert_manager`; no changes needed there (§7 of arch).
- `alert_manager.close()` at process exit is explicitly out-of-scope per architecture §4.1.
