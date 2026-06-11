# PYPOST-498: Architecture

## Plan

1. `validate_environment_rename` in `pypost/core/environment_ops.py` — pure rename rules.
2. `EnvironmentNameDelegate` — validates in `setModelData`, tooltip on reject, callback on accept.
3. `EnvironmentDialog` — set delegate on `env_list`, `_on_environment_renamed` updates model.
4. `_apply_environment_rename` — programmatic/test entry point sharing validation.

## Removed

- `env_list.itemChanged` → `_on_env_item_changed`
- QMessageBox warnings for rename validation
