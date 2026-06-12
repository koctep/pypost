# Environments Dialog

## Overview
The `EnvironmentDialog` class provides the UI for managing environments in PyPost. It allows users to add, delete, and copy environments, as well as modify environment variables and toggle MCP (Model Context Protocol) settings.

## Architecture

User-visible strings (dialog titles, labels, menu actions, validation messages) live in
`pypost/core/environment_messages.py`. UI widgets and `environment_ops.validate_environment_rename`
import constants and small formatter helpers from that module.

`EnvironmentDialog` composes two widgets under `pypost/ui/widgets/environments/`:

- **`EnvironmentListWidget`**: Left pane — `QListWidget`, Add button, F2/context-menu
  rename, copy, and delete. Emits `environment_selected(int)` when the current row changes.
- **`EnvironmentVariablesWidget`**: Right pane — variables `QTableWidget` (Variable / Value /
  Hidden columns) and the MCP checkbox. Loads via `load_environment(Environment | None)` when
  the selection changes.

`EnvPresenter._open_env_manager` passes presenter-owned environments, opens the dialog, then
assigns `self._environments = dialog.environments` before saving — the presenter owns state.

Legacy attributes on `EnvironmentDialog` (`env_list`, `vars_table`, `mcp_check`) delegate to
the child widgets for tests and gradual migration.

## User-visible strings

All Manage Environments copy (window title, button labels, context-menu actions, table
headers, MCP checkbox, validation and confirmation messages) lives in
`pypost/core/environment_messages.py`. Widgets and `collection_item_dialogs` environment
helpers import from that module; rename validation in `environment_ops` uses the same
messages for consistency.

## API / Usage

### `EnvironmentDialog(environments, parent, current_env_name, log_hidden_key_names)`
Initializes the dialog.
- **environments**: List of `Environment` objects to edit. The dialog deep-copies this list
  internally; callers read results via the `environments` property after `exec()`.
- **parent**: The parent widget.
- **current_env_name**: The name of the environment currently active in the application.
- **log_hidden_key_names**: Configuration for logging hidden key names.

### Context Menu Actions (Environment List)
Instead of main UI buttons, actions on existing environments are handled via a right-click context menu on the `env_list`:
- **Rename**: Triggered via `_on_env_list_context_menu` or the `F2` hotkey, it calls `_rename_environment_at_row(row)` to trigger inline editing of the list item. The `itemChanged` signal handles validation and updates the selected environment.
- **Copy**: Triggered via `_on_env_list_context_menu`, it calls `_duplicate_environment_at_row(row)` to create a clone of the selected environment, prompting for a new name.
- **Delete**: Triggered via `_on_env_list_context_menu`, it calls `delete_environment(row)` to remove the selected environment from the list and data model.

### Context Menu Actions (Variables Table)
- **Move Up / Move Down**: Right-clicking a populated variable row allows users to change its relative order in the table using `_move_variable_at_row(row, direction)`. This swaps adjacent items in the ordered `Environment.variables` dict and reloads the table.
- **Delete**: Right-clicking a variable row opens a context menu to delete that specific variable using `_delete_variable_at_row(row)`.

### Variable Editing
- **`on_var_changed(item)`**: Updates the underlying `Environment` object when a user modifies the table. Automatically adds an empty row at the bottom for new variables.
- **`_on_hidden_toggled(checked)`**: Manages the masking and unmasking of hidden variable values in the UI, ensuring the real value is preserved in the item's `UserRole` data.

## Configuration
N/A

## Troubleshooting
- **Hidden Values Losing Data**: Ensure that when `HIDDEN_MASK` is displayed, the real value is stored in `Qt.ItemDataRole.UserRole`. Check `_extract_real_value` and `_make_value_item` for details on how the value is preserved.
- **Duplicate Environment Names**: When copying an environment, the UI validates that the new name is not empty and does not already exist, prompting the user again if invalid.

## Testing

Automated Qt/offscreen coverage lives in `tests/test_env_dialog.py` (module timeout 60s).
The suite exercises:

- Environment list selection, add/delete, and rename validation
- **Copy / duplicate** via `_duplicate_environment_at_row` and context-menu wiring
  (QInputDialog cancel, empty name, duplicate name — patched dialogs/message boxes)
- Variables table: hidden flags, moves, deletes, trailing add row, invalid name revert
- MCP checkbox sync and logging (`caplog` for masked vs readable hidden keys)

Run: `pytest tests/test_env_dialog.py -q`