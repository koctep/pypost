# Architecture: PYPOST-25

## Overview
The task is to extend the functionality of `ResponseView` to support a context menu with the ability to:
1.  Set environment variable values (existing and new).
2.  Copy selected text.

This requires changes in UI components (`ResponseView`, `MainWindow`) and establishing interaction between them via signals.

## Component Diagram
[Diagram]

## Changes in Components

### `ResponseView` (`pypost/ui/widgets/response_view.py`)
Class `ResponseView` is responsible for displaying the response and the context menu.

**Changes:**
-   **Signals**: Update `variable_set_requested(str, str)` signal. First argument is variable name (`None` for new), second is value.
-   **Method `show_context_menu`**:
    -   Rework menu construction logic.
    -   First add "Set env" menu.
    -   Inside "Set env" add list of current keys and "New Variable..." item.
    -   Then add standard "Copy" action (or create custom one if standard doesn't fit order, but `QTextEdit` provides a standard menu that can be modified or created from scratch).
    -   *Decision*: Create menu from scratch, adding `Set env`, then standard actions (Copy).
    -   When "New Variable..." is selected, emit signal with `key=None`.

### `MainWindow` (`pypost/ui/main_window.py`)
Class `MainWindow` manages application state, including environments.

**Changes:**
-   **Method `add_new_tab`**:
    -   Connect `tab.response_view.variable_set_requested` signal to handler slot in `MainWindow`.
-   **Method `on_env_changed`**:
    -   Pass list of keys (`selected_env.variables.keys()`) to `ResponseView` of active tab and all other tabs.
-   **New Method `handle_variable_set_request(key, value)`**:
    -   If `key` is set: update variable in current environment.
    -   If `key` is `None`:
        -   Show `QInputDialog.getText` to enter new variable name.
        -   Validate name (not empty).
        -   Create new variable in current environment.
    -   Save changes via `StorageManager`.
    -   Update `RequestWidget` and `ResponseView` (key list) in all tabs.

## Implementation Plan
1.  Modify `show_context_menu` to implement required order and items.
2.  Ensure correct signal transmission.
3.  Implement variable change handling slot.
4.  Link `ResponseView` signal to this slot.
5.  Ensure key list update in `ResponseView` when environment changes or variable is added.

## Dependencies and Risks
-   **Risk**: Standard `createStandardContextMenu` might contain many unnecessary items.
    -   *Mitigation*: Use only necessary actions (Copy) or create menu entirely manually, adding `copyAvailable` check.
-   **Dependency**: Active environment required. If `env` is `None`, "Set env" menu should not be shown.
