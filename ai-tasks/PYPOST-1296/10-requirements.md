# PYPOST-1296: Public WebSocketPresenter.toggle_connection(); rename routers to toggle

## Goals

1. **Public API Contract**: Add a public `toggle_connection()` method to `WebSocketPresenter`
   to replace external caller dependence on the private UI button slot `_on_connect_clicked()`.
2. **Accurate Semantic Naming**: Rename router functions in
   `pypost/ui/presenters/tabs_presenter_hotkeys.py` from `handle_websocket_connect_global` and
   `handle_mcp_client_connect_global` to `handle_websocket_connect_toggle` and
   `handle_mcp_client_connect_toggle` to accurately describe their bidirectional toggle behavior.
3. **Clean Test Seams**: Update test spy/mock fixtures in `tests/test_main_window_hotkeys.py`
   to patch the public `toggle_connection()` method rather than private internals.
4. **Synchronized Documentation**: Update documentation in `doc/dev/websocket_hotkeys.md`,
   `doc/dev/mcp_client_hotkeys.md`, and `doc/dev/hotkeys.md` to reference the public API and
   renamed router functions.

## User Stories

- As a developer extending WebSocket or MCP hotkey routing, I want router functions to be named
  `handle_*_connect_toggle` so their toggle behavior is immediately obvious from the routing table.
- As a developer maintaining `WebSocketPresenter`, I want external modules to invoke public
  methods (`toggle_connection`) rather than private event slots (`_on_connect_clicked`), preventing
  accidental breakages during UI refactorings.

## Definition of Done

- `WebSocketPresenter.toggle_connection()` added as a public method with docstring.
- `WebSocketPresenter._on_connect_clicked()` delegates directly to `self.toggle_connection()`.
- `pypost/ui/presenters/tabs_presenter_hotkeys.py`:
  - `handle_websocket_connect_global` renamed to `handle_websocket_connect_toggle`.
  - `handle_mcp_client_connect_global` renamed to `handle_mcp_client_connect_toggle`.
  - Backwards-compatibility aliases preserved if needed.
  - `_F5_ROUTES` table references the renamed functions.
  - `handle_websocket_connect_toggle` calls `presenter.toggle_connection()`.
- `tests/test_main_window_hotkeys.py` updated:
  - Spies and mocks target `toggle_connection` instead of `_on_connect_clicked`.
- Documentation in `doc/dev/` updated.
- Quality gates pass: `make lint`, `make typecheck`, and `make verify-ai-tasks`.

## Task Description

In `ai-tasks/PYPOST-1285/60-tech-debt.md` (item TD-9), it was identified that
`handle_websocket_connect_global` called `ws_tab.presenter._on_connect_clicked()`, reaching into a
private button slot of `WebSocketPresenter`. Furthermore, unit tests patched this private slot.
Additionally, both `handle_websocket_connect_global` and `handle_mcp_client_connect_global` toggle
between connected and disconnected states based on current session state, but were named "connect",
making routing tables confusing.

Constraints:
- Implementation language: Python.
- All lines in documentation and markdown <= 100 characters.
- Must execute all commands exclusively through `make`.

## Q&A

- Q: Should `_on_connect_clicked` remain on `WebSocketPresenter`?
  A: Yes, as a private Qt button slot connected to `tab.connect_btn.clicked`, delegating to
  `self.toggle_connection()`.
- Q: Should legacy names (`handle_*_connect_global`) be kept as aliases?
  A: Yes, defining module-level aliases ensures backward compatibility while routing tables
  and new callers use the renamed toggle functions.
