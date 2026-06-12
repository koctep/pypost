# PYPOST-621: Code Cleanup

## Lint / Format

- `read_lints` clean on modified files.
- Alert construction mirrors `main.py` (Path coercion for log path).

## Review Notes

- `_alert_settings_changed` is a pure comparator — easy to unit test indirectly via
  `open_settings` tests.
- `set_alert_manager` is a narrow setter; no worker pool iteration required.

## Files Touched

| File | Notes |
| --- | --- |
| `pypost/ui/main_window.py` | +~30 LOC |
| `pypost/ui/presenters/tabs_presenter.py` | +6 LOC |
| `tests/test_main_window_alert_reload.py` | New module |
