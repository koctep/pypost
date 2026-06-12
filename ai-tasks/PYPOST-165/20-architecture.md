# Architecture: PYPOST-165

## Overview

Extend Manage Environments variable editing so invalid keys are rejected with the shared core
validator and the same QMessageBox helper used by `EnvPresenter`.

## Changes Summary

### `EnvironmentVariablesWidget._sync_env_variables_from_table`

**Current behaviour (after PYPOST-471):** Invalid keys are skipped and the edited cell reverts
silently.

**New behaviour:** After revert, call `show_invalid_variable_name_error(self, error)` with the
message from `validate_environment_variable_name`.

## Component Changes

| Component | Change |
| --- | --- |
| `environment_variables_widget.py` | Import dialog helper; show error on COL_VAR edit failure |
| `environment_ops.py` | No change — already delegates to `validate_variable_name` |
| `collection_item_dialogs.py` | No change — reuse `show_invalid_variable_name_error` |

## Validation Rules

Same as `pypost/core/variable_name_validation.py` (documented in `doc/dev/variable_validation.md`).

## Testing

- `tests/test_env_dialog.py` — patch `show_invalid_variable_name_error`; assert call on new
  row and rename-to-invalid paths.
- `tests/test_environment_ops.py` — unit tests for `validate_environment_variable_name` wrapper.
