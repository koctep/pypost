# PYPOST-472: Code Cleanup

## Changes

- Removed 5-line duplicate empty-name check in `env_presenter.py`.
- Single validation path: strip → `_is_valid_variable_name` → QMessageBox on failure.

## Quality

- No unused imports introduced.
- Presenter still owns dialog title; core owns message body.
