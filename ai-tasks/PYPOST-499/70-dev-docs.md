# PYPOST-499: Dev Docs

No `doc/dev/` updates required. Existing
[environment_encryption_at_rest.md](../../doc/dev/environment_encryption_at_rest.md) documents
`MainWindow.open_settings()` → `apply_encryption_settings()` wiring. This task adds
automated regression coverage only.

**Test location:** `tests/test_settings_encryption_main_window_e2e.py`
