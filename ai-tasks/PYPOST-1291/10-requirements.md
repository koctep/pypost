# PYPOST-1291: Remove uncalled TabsPresenter hotkey facade methods

## Goals

During PYPOST-1285, hotkey routing was refactored so that `F5` and `Ctrl+Return` dispatch via
`TabsPresenter.handle_f5_global()` and `TabsPresenter.handle_ctrl_return_global()`, delegating directly
to module-level route tables in `pypost/ui/presenters/tabs_presenter_hotkeys.py`.

However, four legacy facade methods remain on `TabsPresenter`:
- `handle_websocket_connect_global(self)`
- `handle_websocket_send_message_global(self)`
- `handle_mcp_client_connect_global(self)`
- `handle_mcp_client_invoke_global(self)`

These facades have no production callers. They suggest incorrect entry points for keyboard shortcut wiring
(bypassing the `hotkey_routed` event logging) and add unnecessary lines to `TabsPresenter`, which is
tightly managed against its baseline metrics cap in `ai-tasks/PYPOST-376/baseline-metrics.md`.

The goal of this task is to:
1. Eliminate the four dead facade methods from `TabsPresenter`.
2. Update tests in `tests/test_main_window_hotkeys.py` to test through `handle_f5_global()` and
   `handle_ctrl_return_global()`.
3. Lower the measured LOC baseline for `tabs_presenter.py` in `ai-tasks/PYPOST-376/baseline-metrics.md`.

## User Stories

- As a developer maintaining PyPost, I want hotkey routing dispatch to have a single, unified entry
  point (`handle_f5_global` and `handle_ctrl_return_global`), so that all shortcut dispatches consistently
  log `hotkey_routed` events and follow route tables.
- As a maintainer auditing codebase complexity, I want dead facade wrappers removed from `TabsPresenter`,
  reducing LOC in core presenter modules.

## Definition of Done

This task is considered `done` when:
1. The four uncalled facade methods (`handle_websocket_connect_global`, `handle_websocket_send_message_global`,
   `handle_mcp_client_connect_global`, and `handle_mcp_client_invoke_global`) are removed from `TabsPresenter`.
2. `tests/test_main_window_hotkeys.py` calls `handle_f5_global()` and `handle_ctrl_return_global()` on the
   corresponding tab states rather than calling deleted facades.
3. Module-level routing functions in `tabs_presenter_hotkeys.py` remain accessible to route tables.
4. `ai-tasks/PYPOST-376/baseline-metrics.md` is updated with the lowered measured LOC for `tabs_presenter.py`.
5. All test suites pass without regression (`make check` quality gate passes).

## Task Description

### Problem Description
`TabsPresenter` contains redundant facade methods that merely wrap `tab_hotkeys.<method>(self)` after an
`_admission_open()` check. Following the PYPOST-1285 routing overhaul, `main_window.py` only binds `F5` and
`Ctrl+Return` to `handle_f5_global` and `handle_ctrl_return_global`. The individual protocol facades are dead
code in production.

### Scope
- Remove the four dead facades from `pypost/ui/presenters/tabs_presenter.py`.
- Update tests in `tests/test_main_window_hotkeys.py` that directly invoked the facades.
- Update baseline metrics in `ai-tasks/PYPOST-376/baseline-metrics.md`.
- Preserve `handle_websocket_format_json_global`, which is still a live binding from `main_window_protocol_hotkeys.py`
  for `Ctrl+Shift+F`.
- Preserve module-level route functions in `pypost/ui/presenters/tabs_presenter_hotkeys.py`.

### Non-Functional Requirements
- Maintain code cleanliness and reduce unnecessary LOC.
- Ensure all tests pass with explicit timeout markers.

### Constraints and Assumptions
- Implementation language: Python.
- `TabsPresenter` must preserve active bindings (`handle_f5_global`, `handle_ctrl_return_global`,
  `handle_websocket_format_json_global`, `handle_focus_url`, `handle_switch_to_*_global`).

## Q&A

- **Q: Why keep `handle_websocket_format_json_global` on `TabsPresenter`?**
  **A:** Unlike the four removed facades, `handle_websocket_format_json_global` is actively bound to
  `Ctrl+Shift+F` in `main_window_protocol_hotkeys.py` (`register_protocol_session_hotkeys`).
- **Q: Are module-level functions in `tabs_presenter_hotkeys.py` affected?**
  **A:** No, the module-level functions (`handle_websocket_connect_global`, etc.) are referenced by the
  route tables `_F5_ROUTES` and `_CTRL_RETURN_ROUTES`. Only the uncalled class facade methods on
  `TabsPresenter` are removed.
