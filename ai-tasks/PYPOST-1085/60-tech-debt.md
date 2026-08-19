# Technical Debt Analysis: PYPOST-1085

## Resolved Debt

- **D7 / F9 from PYPOST-1071**: `for_window` back-reference coupling `McpServerSettingsController` back to `MainWindow` and importing `MainWindow` as a type cycle guard has been removed; construction is directly inlined in `MainWindow.__init__`.
- **D9 / F9 from PYPOST-1071**: `MainWindow`'s re-published `self.mcp_manager` and `self.mcp_registry` attribute aliases have been dropped. Collaborators now access `mcp_controller.manager` and `mcp_controller.registry` directly.

## New Debt Introduced

- **None**: This refactor simplifies dependencies and cleans up transitional aliases.

## Follow-up Tasks

- Pre-existing tasks remaining in the sprint backlog: PYPOST-1087, PYPOST-1090, PYPOST-1091.
