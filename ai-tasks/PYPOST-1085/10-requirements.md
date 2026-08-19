# Requirements: PYPOST-1085

## Summary

Drop the `MainWindow` back-reference (`for_window` factory method in `McpServerSettingsController`) and the re-published `mcp_manager` / `mcp_registry` attribute aliases on `MainWindow`.

## Background & Motivation

Follow-up F9 from PYPOST-1071 (items D7 and D9):
1. **D7: `for_window` back-reference and partially-built window**:
   `McpServerSettingsController.for_window(window: MainWindow)` coupled the controller back to `MainWindow`, importing it under `TYPE_CHECKING` as an import cycle guard. Inlining construction into `MainWindow.__init__` removes the back-reference while keeping the lazy collaborator lookups.
2. **D9: `MainWindow` re-publishes what the controller now owns**:
   `MainWindow` assigned `self.mcp_manager = self.mcp_controller.manager` and `self.mcp_registry = self.mcp_controller.registry` purely as transitional backward-compatibility aliases during extraction. These aliases bypass the controller seam.

## Requirements

1. **Remove `for_window`**:
   - In `pypost/ui/mcp_server_controller.py`, remove the `for_window` classmethod and the `from pypost.ui.main_window import MainWindow` TYPE_CHECKING block.
   - In `pypost/ui/main_window.py`, directly instantiate `McpServerSettingsController(...)` in `MainWindow.__init__`.

2. **Remove `MainWindow` Aliases**:
   - Remove `self.mcp_manager` and `self.mcp_registry` from `MainWindow`.
   - Update `pypost/ui/main_window.py` to pass `self.mcp_controller.manager` and `self.mcp_controller.registry` into `EnvPresenter`.
   - Update `pypost/main.py:136` to read `window.mcp_controller.registry`.

3. **Update Tests**:
   - In `tests/test_main_window.py`, assert `self.assertIs(mcp_manager, window.mcp_controller.manager)` and verify `MainWindow` has no `mcp_manager` or `mcp_registry` attributes.

4. **Update Documentation**:
   - Update `doc/dev/mcp_integration.md` and `doc/dev/testability.md` to reflect direct instantiation and access via `window.mcp_controller`.
