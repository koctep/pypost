# Environments Dialog

## Overview
The `EnvironmentDialog` class provides the UI for managing environments in PyPost. It allows users to add, delete, and copy environments, as well as modify environment variables and toggle MCP (Model Context Protocol) settings.

## Architecture
- **Environment List (`env_list`)**: A `QListWidget` on the left side displaying all available environments. Actions for environments are accessed via a context menu.
- **Variables Table (`vars_table`)**: A `QTableWidget` on the right side for editing variables of the currently selected environment. It includes columns for "Variable", "Value", and "Hidden".
- **MCP Checkbox (`mcp_check`)**: A toggle to enable or disable the Model Context Protocol for the selected environment.

## API / Usage

### `EnvironmentDialog(environments, parent, current_env_name, log_hidden_key_names)`
Initializes the dialog.
- **environments**: List of `Environment` objects to manage.
- **parent**: The parent widget.
- **current_env_name**: The name of the environment currently active in the application.
- **log_hidden_key_names**: Configuration for logging hidden key names.

### Context Menu Actions (Environment List)
Instead of main UI buttons, actions on existing environments are handled via a right-click context menu on the `env_list`:
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