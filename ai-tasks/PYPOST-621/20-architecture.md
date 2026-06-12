# PYPOST-621 Architecture — AlertManager reload on settings save

## 1. Problem Summary

`AlertManager` is created once in `main.py` and injected into `MainWindow` →
`TabsPresenter` → `RequestWorker`. `MainWindow.open_settings` persisted alert fields
(PYPOST-439) but left the running instance unchanged.

## 2. Solution Overview

Mirror the existing `metrics_changed` pattern in `open_settings`:

1. Compare previous vs new `AppSettings` for the three alert fields.
2. On change, call `_reload_alert_manager()`:
   - `close()` previous instance if present
   - Construct `AlertManager` with same parameters as `main.py`
   - `TabsPresenter.set_alert_manager(new_instance)`

In-flight workers retain their injected manager; only new executions pick up the reload.

## 3. Files Changed

| File | Change |
| --- | --- |
| `pypost/ui/main_window.py` | `_alert_settings_changed`, `_reload_alert_manager`, hook in `open_settings` |
| `pypost/ui/presenters/tabs_presenter.py` | `set_alert_manager` |
| `tests/test_main_window_alert_reload.py` | Reload and skip-path tests |
| `doc/dev/settings_dialog.md` | Replace limitation with runtime reload section |

## 4. Risks

| Risk | Mitigation |
| --- | --- |
| Handler accumulation | `close()` on old instance before creating new |
| Stale webhook on running worker | Documented: in-flight requests unchanged (acceptable) |
