# PYPOST-598: Code Cleanup

## Actions

- Split monolithic `settings_dialog.py` (~576 LOC) into eight domain section builders under
  `pypost/ui/widgets/settings/`.
- `settings_dialog.py` is now a thin coordinator (~185 LOC): composes sections, mirrors widget
  attributes for tests, delegates `accept()` validation/collect.
- Preserved public re-exports on `settings_dialog` module (`KEY_SOURCE_*`, `ENCRYPTION_MODE_*`,
  `parse_env_encryption_enabled_from_mode`, webhook helpers, patch-target dialog functions).
- Added `# noqa: F401` on intentional re-export import blocks to satisfy flake8.

## Lint / format

| Scope | Result |
| --- | --- |
| `pypost/ui/dialogs/settings_dialog.py` | Clean |
| `pypost/ui/widgets/settings/` | Clean |
| Repo-wide `make lint` | Pre-existing issues outside this task (`encryption_migration.py`,
  `encryption_migration_worker.py`, `mixins.py`, `request_editor.py`) — not introduced here |

- Line length within project 100-character limit in all touched files.
- UTF-8, LF, trailing whitespace removed, final newline on all new modules.

## Test run

```text
69 passed — test_settings_dialog, test_settings_encryption,
  test_settings_encryption_migration_ui, test_settings_persistence,
  test_settings_encryption_main_window_e2e, test_settings_key_source_main_window_e2e
```
