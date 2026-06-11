# PYPOST-544: Code Cleanup

## Lint / format

- No new lint issues in modified files.
- Line length within 100 characters.

## Review notes

- Stats formatting kept inline in `_format_migration_report` (matches existing inventory lines).
- No shared helper extracted — CLI and Settings label styles differ intentionally.

## Files touched

- `pypost/ui/dialogs/settings_dialog.py`
- `tests/test_settings_encryption_migration_ui.py`
