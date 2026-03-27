# Hidden Variables

## Overview

PYPOST-437 adds a `hidden` flag for environment variables. Hidden variables are masked in UI
surfaces to reduce accidental secret exposure during screen sharing and day-to-day editing.

The feature is display-level only: request execution still uses real values from
`Environment.variables`.

## Architecture

- **Model**: `pypost.models.models.Environment`
  - Adds `hidden_keys: Set[str]`.
- **Environment Manager UI**: `pypost.ui.dialogs.env_dialog.EnvironmentDialog`
  - Adds `Hidden` checkbox column.
  - Masks value cell as `********` when hidden.
  - Stores real hidden value in `QTableWidgetItem` `UserRole` to keep edits/renames safe.
- **Hover resolution**: `pypost.ui.widgets.mixins.VariableHoverHelper`
  - Returns mask for hidden keys in tooltips/preview.
- **Signal propagation**:
  - `EnvPresenter.env_hidden_keys_changed`
  - `TabsPresenter.on_env_hidden_keys_changed`
  - `RequestWidget.set_hidden_keys`
  - Variable-aware widgets consume hidden key set for hover masking.
- **Persistence**: `pypost.core.storage.StorageManager`
  - JSON-safe serialization via `model_dump(mode="json")`.
  - Atomic write (`.tmp` + `os.replace`) for `environments.json`.

## Usage

1. Open **Manage Environments**.
2. Mark variable row as **Hidden**.
3. Value column shows `********`; hover previews also show mask.
4. Uncheck **Hidden** to reveal value again.

Cloning environments preserves hidden flags (`clone_environment` copies `hidden_keys`).

## Configuration

No new runtime settings were introduced for this feature.

## Troubleshooting

- **Environments disappear / file corruption concerns**
  - Verify `StorageManager.save_environments` uses atomic save path and no local patch reverted it.
  - Run tests:
    - `tests/test_storage_environments.py`
    - `tests/test_env_persistence_e2e.py`
- **Hidden value lost after rename/edit**
  - Check `EnvironmentDialog` value-cell `UserRole` handling and related tests:
    - `tests/test_env_dialog.py`

## Security Notes

- Hidden flag does **not** encrypt values at rest.
- Hidden flag does **not** change request runtime substitution.
- Follow-up debts for stronger protections are tracked in Jira:
  - `PYPOST-446`, `PYPOST-447`, `PYPOST-448`, `PYPOST-449`.
