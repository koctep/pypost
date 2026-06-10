# Hidden Variables

## Overview

PYPOST-437 adds a `hidden` flag for environment variables. Hidden variables are masked in UI
surfaces to reduce accidental secret exposure during screen sharing and day-to-day editing.

The feature is display-level only: request execution still uses real values from
`Environment.variables`.

PYPOST-446 masks hidden-derived values in request history. PYPOST-448 adds a configurable
logging policy for hidden-flag toggle events (variable key names in diagnostic logs).

## Architecture

- **Model**: `pypost.models.models.Environment`
  - Adds `hidden_keys: Set[str]`.
- **Environment Manager UI**: `pypost.ui.dialogs.env_dialog.EnvironmentDialog`
  - Adds `Hidden` checkbox column.
  - Masks value cell as `********` when hidden.
  - Stores real hidden value in `QTableWidgetItem` `UserRole` to keep edits/renames safe.
  - Emits `env_hidden_flag_changed` INFO log on toggle (key name policy: PYPOST-448).
  - PYPOST-467: context-menu **Delete** on populated variable rows (see
    [Environment Variable Delete](environment_variable_delete.md)).
- **Toggle log policy**: `pypost.core.hidden_toggle_log_policy.HiddenToggleLogPolicy`
  - Formats variable key name for `env_hidden_flag_changed` log events.
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

### Hidden-flag toggle logging (PYPOST-448)

Setting: `AppSettings.log_hidden_key_names` (persisted in `settings.json`).

| Value | UI checkbox | Toggle log `key` field |
|-------|-------------|-------------------------|
| `False` (default) | unchecked | `********` (`HIDDEN_MASK`) |
| `True` | checked | actual variable name |

Enable in **Settings** → **Log variable key names when hidden flag is toggled**.

**Breaking change vs PYPOST-437**: key names were always logged before PYPOST-448. Default is
now redacted; enable the checkbox for full key-name diagnostics.

Policy is snapshotted when **Manage Environments** opens. Change the setting, save, then
reopen the dialog for the new policy to apply.

Variable values are never written to toggle logs in either mode.

### API

```python
from pypost.core.hidden_toggle_log_policy import HiddenToggleLogPolicy

# Default (suppressed)
HiddenToggleLogPolicy.format_key_name("API_KEY", log_hidden_key_names=False)
# -> "********"

# Opt-in full visibility
HiddenToggleLogPolicy.format_key_name("API_KEY", log_hidden_key_names=True)
# -> "API_KEY"
```

## Troubleshooting

- **Environments disappear / file corruption concerns**
  - Verify `StorageManager.save_environments` uses atomic save path and no local patch reverted it.
  - Run tests:
    - `tests/test_storage_environments.py`
    - `tests/test_env_persistence_e2e.py`
- **Hidden value lost after rename/edit**
  - Check `EnvironmentDialog` value-cell `UserRole` handling and related tests:
    - `tests/test_env_dialog.py`
- **Toggle logs show `********` instead of key names**
  - Expected default (`log_hidden_key_names=False`). Enable the Settings checkbox if your
    org policy allows key-name logging for diagnostics.
- **Setting change does not affect an open Manage Environments dialog**
  - Close and reopen the dialog; policy is read at construction time.

## Security Notes

- Hidden flag alone is still a display-level control.
- At-rest protection is available separately via PYPOST-447 encryption flow.
- Runtime request substitution still uses real values after load-time resolution.
- Toggle logs never include variable values; key names are redacted by default (PYPOST-448).
- See `doc/dev/environment_encryption_at_rest.md` for encryption configuration and behavior.

## Related Tests

- `tests/test_hidden_toggle_log_policy.py`
- `tests/test_env_dialog.py` (caplog: masked vs readable key)
- `tests/test_settings_dialog.py` (checkbox load/save)
- `tests/test_settings_persistence.py` (legacy settings without field)
- `tests/test_settings_hidden_toggle_logging_e2e.py` (PYPOST-490: Settings →
  `apply_settings` → env manager → toggle log; default masked and opt-in readable key)
