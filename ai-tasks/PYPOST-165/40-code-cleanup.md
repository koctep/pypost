# PYPOST-165: Code Cleanup

## Changes

- Single import and one call site in `environment_variables_widget.py`.
- Test assertions use existing mock/patch patterns from `test_env_dialog.py`.

## Lint / Format

- No new linter issues introduced.
- Line length within project limits.

## Test Run

- `pytest tests/test_env_dialog.py tests/test_environment_ops.py -q`
