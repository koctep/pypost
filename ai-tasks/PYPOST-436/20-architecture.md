# PYPOST-436: Remove Delete button from Environments window and move action to context menu

## Research

Analyzed `pypost/ui/dialogs/env_dialog.py`, specifically the `EnvironmentDialog` class.
- The "Delete" button is currently instantiated in `init_ui` as `del_btn = QPushButton("Delete")` and added to `left_layout`.
- The `env_list` (a `QListWidget`) already uses a custom context menu policy and connects `customContextMenuRequested` to `_on_env_list_context_menu`.
- `_on_env_list_context_menu` creates a `QMenu`, currently offering only a "Copy" action.
- The `delete_environment` method relies on `self.env_list.currentRow()`.

## Implementation Plan

1. In `pypost/ui/dialogs/env_dialog.py`:
   - Remove the `del_btn` creation and its addition to `left_layout`.
   - Modify `_on_env_list_context_menu` to include a "Delete" action in the `QMenu` alongside the existing "Copy" action.
   - Refactor `delete_environment` to optionally accept a `row: int` argument (or introduce a new `_delete_environment_at_row(self, row: int)` method) so that the specific environment clicked via the context menu is correctly removed, mirroring the approach used for `_duplicate_environment_at_row`.
2. Ensure no regressions occur in existing deletion logic. Safety checks and confirmations (if any are introduced later or currently exist implicitly) must remain intact.

## Architecture

No new major modules, patterns, or dependencies are introduced. The architectural change is strictly within the internal event-handling of the UI view component.

- **Module Affected**: `pypost.ui.dialogs.env_dialog`
- **Component**: `EnvironmentDialog`
- **Data Flow**: The deletion trigger shifts from `QPushButton.clicked` to `QAction.triggered` within a `QMenu` context event. The underlying data modification (removing the environment from `self.environments` and `self.env_list`) remains identical.

## Q&A

*(No questions at this time)*
