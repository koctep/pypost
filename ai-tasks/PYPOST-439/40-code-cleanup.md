# PYPOST-439: Code Cleanup

## Lint / Format

- No new linter issues in modified files (`read_lints` clean).
- Imports grouped: stdlib (`pathlib`), third-party (`platformdirs`, PySide6), local.

## Review Notes

- `_resolve_webhook_auth_header` is a pure helper — unit-tested without Qt.
- `alert_webhook_auth_clear_check` widget always exists; form row added only when auth was
  stored (avoids empty row for new installs).
- Constants `WEBHOOK_AUTH_*_PLACEHOLDER` exported for test assertions.

## Files Touched

| File | Notes |
| --- | --- |
| `pypost/ui/dialogs/settings_dialog.py` | +~45 LOC net |
| `tests/test_settings_dialog.py` | New alert-settings test classes |
