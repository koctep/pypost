# Environment Management and Variable Display

## Overview

The Environment Management system in PyPost allows users to organize, edit, import, and export key-value variables across development, staging, production, and testing contexts.

When opening the **Manage Environments** dialog from the main window (via the "Manage" button or keyboard shortcut), the dialog provides immediate visibility into the active environment's variables and settings. The dialog coordinates the left-pane environment selection list with the right-pane variables editor table, ensuring that the selected environment's variables, masked secrets, and Model Context Protocol (MCP) server configuration are populated synchronously on initial open and reactively on any selection change or list mutation.

## Architecture

Environment management follows a composite Model-View-Presenter (MVP) architecture:

```
+-------------------------------------------------------------------------+
|                              EnvPresenter                               |
| (Coordinates MainWindow combo selector, Storage gateway, domain signals) |
+-------------------------------------------------------------------------+
                                    |
                                    | creates & exec()
                                    v
+-------------------------------------------------------------------------+
|                           EnvironmentDialog                             |
|    (Composite View & Mediator between list and variable table widgets)   |
|                                                                         |
|  +-----------------------------+     +-------------------------------+  |
|  |    EnvironmentListWidget    |     |  EnvironmentVariablesWidget   |  |
|  |  (Left Pane: QListWidget)   |     | (Right Pane: QTableWidget)    |  |
|  | - Environments working list |     | - Variable key/value editing  |  |
|  | - Add / Delete / Import     |     | - Secret mask checkbox        |  |
|  | - Selection state           |     | - MCP enablement checkbox     |  |
|  +-----------------------------+     +-------------------------------+  |
|                 |                                    ^                  |
|                 +--- environment_selected(int) ------+                  |
+-------------------------------------------------------------------------+
```

### Component Roles

1. **`EnvPresenter`** (`pypost/ui/presenters/env_presenter.py`):
   - Owns top-bar combo selection, workspace environment storage persistence, and encryption keys.
   - Extracts the currently active environment name (`current_env_name = self._env_selector.currentText()` or `None` if "No Environment" is selected).
   - Instantiates `EnvironmentDialog(self._environments, self._widget, current_env_name=current_env_name, ...)`.
   - On dialog accept/close, updates presenter-owned environment state and triggers save.
   - Emits decoupled domain Qt signals (`environment_selected`, `environment_updated`, `environment_manager_closed`) wired centrally in `main_window_signals.py` to notify MCP controls and tab editors without direct cross-presenter calls. See [Environment-to-MCP State Propagation](environment_mcp_signals.md).

2. **`EnvironmentDialog`** (`pypost/ui/dialogs/env_dialog.py`):
   - Acts as the mediator between the list and variables subwidgets.
   - Assembles `EnvironmentListWidget` (left pane) and `EnvironmentVariablesWidget` (right pane).
   - Connects `self._env_list_widget.environment_selected` to `self.on_env_selected`.
   - **Initial Synchronization**: Immediately during `__init__`, calls `self.on_env_selected(self.env_list.currentRow())` to load the initial environment into the variables table.

3. **`EnvironmentListWidget`** (`pypost/ui/widgets/environments/environment_list_widget.py`):
   - Renders the list of environments in a `QListWidget`.
   - Selects the target row corresponding to `current_env_name` (or row 0 if `current_env_name` is `None` or not found).
   - **Signal Emission on Mutations**: Explicitly emits `self.environment_selected.emit(self.env_list.currentRow())` across all list-mutating operations:
     - `load_list()`: After clearing and populating items.
     - `add_environment()`: After adding a new environment item and selecting its row.
     - `delete_environment(row)`: After removing an environment item and updating row selection.
     - `import_environments()`: After applying an import plan and refreshing via `load_list()`.

4. **`EnvironmentVariablesWidget`** (`pypost/ui/widgets/environments/environment_variables_widget.py`):
   - Renders the variable key-value table and MCP toggle checkbox.
   - `load_environment(env: Environment | None)`:
     - If `env` is `None`: Clears the table (0 rows), unchecks and disables `mcp_check`.
     - If `env` is an `Environment`: Populates the table with existing variables plus 1 trailing row for adding new entries, applies secret masking for keys in `hidden_keys`, and syncs `mcp_check` state and enablement.

## UI Behavior & Lifecycle

### Active Environment Selection

1. When opening the dialog with an active environment (e.g. `"Staging"`):
   - `EnvironmentListWidget` sets current row to the matching `"Staging"` item.
   - `EnvironmentDialog.__init__` invokes `on_env_selected(row)`.
   - `EnvironmentVariablesWidget` immediately renders all `"Staging"` variables and reflects its MCP setting.

### Fallback Behavior: "No Environment" Selected

1. When opening the dialog with "No Environment" (`current_env_name=None` or unassigned):
   - If environments exist: `EnvironmentListWidget` defaults selection to row 0 (the first available environment), and `EnvironmentDialog` immediately displays row 0's variables.
   - If no environments exist in the workspace: The list is empty (`currentRow() == -1`), and `EnvironmentVariablesWidget.load_environment(None)` clears the table and disables the MCP checkbox.

### Switching Environments Inside Dialog

1. When the user selects a different environment row in the list:
   - `EnvironmentListWidget` emits `environment_selected(int)`.
   - `EnvironmentDialog.on_env_selected(row)` fetches the target `Environment` at `row` and invokes `EnvironmentVariablesWidget.load_environment(env)`.
   - The table immediately updates to show the selected environment's variables and MCP status.

### Adding and Deleting Environments

- **Adding an Environment**: Prompts for a name; upon confirmation, creates a new environment, appends it to the list, selects the new row, and emits `environment_selected`. The table is displayed with an empty variable set and a trailing add row.
- **Deleting an Environment**: Prompts for confirmation; upon confirmation, removes the environment, adjusts the list, and emits `environment_selected(self.env_list.currentRow())`. If other environments remain, the newly selected row's variables are displayed; if the list is now empty, the table is cleared and disabled.

## Automated Tests & Regression

Automated Qt tests reside in `tests/test_env_dialog.py` (with module timeout `pytestmark = pytest.mark.timeout(60)` and test timeouts `@pytest.mark.timeout(10)`):

| Test Case | Scenario Verified |
| --- | --- |
| `test_dialog_init_immediately_loads_current_environment_variables` | Opening dialog with an active environment immediately populates variables table and MCP settings without manual intervention. |
| `test_dialog_init_with_no_env_specified_loads_first_env` | Opening dialog with `current_env_name=None` falls back to row 0 and immediately populates table with the first environment's variables. |
| `test_dialog_init_with_empty_environments_leaves_table_empty_and_disabled` | Opening dialog with an empty list (`[]`) leaves list row at -1, table with 0 rows, and MCP toggle disabled. |
| `test_dialog_switching_environment_updates_variables_table` | Changing row selection back and forth updates variables and MCP checkbox immediately. |
| `test_dialog_add_environment_updates_variables_table` | Adding a new environment selects the newly added row and displays empty variable table ready for input. |
| `test_dialog_delete_environment_updates_variables_table` | Deleting an environment updates the current row selection and refreshes the variable table. |

Run tests via:
```bash
pytest tests/test_env_dialog.py -q
```

## Variable Template Resolution

Environment variables can contain template expressions and built-in function calls (e.g. `{{ env(API_KEY) }}` or `{{ host }}:{{ port }}`).
Resolution is handled by `EnvironmentVariableResolver` (`pypost/core/environment_variable_resolver.py`), which:
- Resolves cross-variable references recursively up to a depth limit (32).
- Executes built-in functions registered in `FunctionRegistry`.
- Detects circular dependency cycles (e.g., `A -> B -> A`), logging a warning and preserving the unrendered token to prevent infinite loops.
- Automatically resolves environment variables before request dispatch in `HTTPClient`, `RequestService`, and hover previews in `VariableHoverResolver`.

## Troubleshooting

- **Variables Table Empty on Dialog Open**: Check `EnvironmentDialog.__init__` to verify that `self.on_env_selected(self.env_list.currentRow())` is invoked after signal connections.
- **Stale Variables After List Mutation**: Verify that mutating actions in `EnvironmentListWidget` (`load_list`, `add_environment`, `delete_environment`) emit `self.environment_selected.emit(self.env_list.currentRow())`.
