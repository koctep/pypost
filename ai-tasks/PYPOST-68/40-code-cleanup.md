# PYPOST-68: Code Cleanup

## Changes

- Removed unused widget-exposure properties (dead after PYPOST-106).
- Consolidated font application in `apply_font`.
- Tests use `_env_selector` only for artificial setup bypassing `load_environments`.

## No further cleanup required

Presenter API is now consistent with encapsulation goal.
