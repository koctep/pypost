# PYPOST-496: Code Cleanup

## Actions

- Removed duplicated UI setup from `env_dialog.py`; dialog is now a thin composer.
- Grouped new widgets under `pypost/ui/widgets/environments/` (not `env/` — collides with
  `.gitignore` `ENV/` rule) with `__init__.py` exports.
- Updated test patches to target modules where `QInputDialog`, `confirm_delete_environment`,
  and `QMenu.exec` are now imported.

## Lint / format

- No new flake8 issues in touched files.
- Line length within project 100-character limit.

## Test run

```text
39 passed — test_env_dialog, test_env_persistence_e2e, test_settings_hidden_toggle_logging_e2e
```
