# PYPOST-365: Code Cleanup

## Lint and Format

- `flake8` clean on new test module and `tests/conftest.py` changes.
- Imports ordered: `pytest` / `pytestmark` before third-party before local (matches existing GUI tests).

## Conventions Applied

- Module docstring cites PYPOST-365 and PYPOST-37.
- `try` / `finally` / `view.close()` teardown pattern from `test_env_dialog.py`.
- No trailing whitespace; UTF-8 LF; max 100 columns.

## Not Changed

- Existing per-module `qapp` fixtures left in place to minimize diff scope.
