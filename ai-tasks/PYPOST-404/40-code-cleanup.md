# PYPOST-404 — Code Cleanup

**Date**: 2026-03-25
**Author**: junior_engineer

---

## Summary

Implementation is complete and all tests pass (191 passed, 0 failed). The changes are minimal
and surgical; no structural cleanup was required beyond the fix itself.

---

## Changes Made

### `pypost/ui/main_window.py`

1. **FR-1/FR-2/FR-3 — Fixed `apply_settings` call order**
   - Moved `self.style_manager.apply_styles(app)` before `font = app.font()` and
     `app.setFont(font)`, so the stylesheet re-polish happens first and the font is set
     after, surviving the Qt re-polish cycle.

2. **FR-4 — Added optional `config_manager` constructor parameter**
   - Signature: `config_manager: ConfigManager | None = None`
   - Uses the injected instance when provided; falls back to `ConfigManager()` otherwise.
   - Eliminates the duplicate `load_config()` call when `main.py` passes its instance.

### `pypost/main.py`

- Passes `config_manager=config_manager` to `MainWindow(...)`, completing the FR-4 injection.

### `tests/test_apply_settings_font.py` (new)

- Implements T-1, T-2, T-3 as specified in `20-architecture.md`.
- Uses `patch.object(window.style_manager, "apply_styles", side_effect=lambda app:
  app.setStyleSheet(""))` to reproduce the real-world re-polish reset in isolation.
- Module-scoped `qapp` fixture avoids duplicate `QApplication` errors across the suite.

---

## Code Quality Checklist

- [x] No trailing whitespace
- [x] Single final newline in all modified files
- [x] Line length ≤ 100 characters
- [x] No dead code introduced
- [x] No duplicate logic introduced (FR-4 removes duplication)
- [x] All new code in English
- [x] Full test suite passes: 191 passed, 0 failed

---

## No Further Cleanup Required

The fix is two logical changes (reorder + optional injection). No abstractions were introduced,
no helpers were added, and no existing functionality was altered beyond the documented fix scope.
