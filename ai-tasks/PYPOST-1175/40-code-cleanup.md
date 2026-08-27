# PYPOST-1175: Code Cleanup

## Changes

- `pypost/ui/main_window_protocol_hotkeys.py` — extracted protocol session hotkey registration
- Added `invoke_form` property on `McpClientTab` mirroring `WebSocketTab.composer`.
- Fixed `_setup_save_shortcuts` to bind Ctrl+S/Ctrl+Shift+S (was help-tag only).

## No further cleanup required

Routing logic is symmetric with WebSocket handlers; no dead code introduced.
