# Architecture: PYPOST-1296 — Public WebSocket toggle_connection & Router Rename

## Research

1. **Current State in `pypost/ui/presenters/websocket_presenter.py`**:
   `WebSocketPresenter` contains `_on_connect_clicked(self)` which implements connect/disconnect
   branching depending on `self.state`. Because this was a private button slot, other modules
   invoked private internals.
2. **Current State in `pypost/ui/presenters/tabs_presenter_hotkeys.py`**:
   - `handle_websocket_connect_global` delegates directly to
     `ws_tab.presenter._on_connect_clicked()`.
   - `handle_mcp_client_connect_global` checks `mcp_tab.presenter.state` and calls either
     `disconnect_requested()` or `connect_requested()`.
   - Both functions toggle state, but are named `*_connect_global`.
   - In `_F5_ROUTES`, the action name is `"connect_toggle"`, which mismatches the function names.
3. **Current State in `tests/test_main_window_hotkeys.py`**:
   - Tests spy/mock `tab.presenter._on_connect_clicked`.
4. **Current State in Dev Docs**:
   - `doc/dev/websocket_hotkeys.md`, `doc/dev/mcp_client_hotkeys.md`, and `doc/dev/hotkeys.md`
     document `handle_*_connect_global` and the private `_on_connect_clicked` call.

## Implementation Plan

### Step 3: Failing Repro Test
- Add unit tests in `tests/test_main_window_hotkeys.py`:
  - `test_websocket_presenter_exposes_public_toggle_connection`:
    Verifies `hasattr(WebSocketPresenter, "toggle_connection")`.
  - `test_router_functions_renamed_to_toggle`:
    Verifies `handle_websocket_connect_toggle` and `handle_mcp_client_connect_toggle` are
    exported by `tabs_presenter_hotkeys` and bound in `_F5_ROUTES`.
- Both tests will fail prior to implementation in Step 4.

### Step 4: Development
1. **`pypost/ui/presenters/websocket_presenter.py`**:
   - Add public `toggle_connection(self) -> None`.
   - Update `_on_connect_clicked(self) -> None` to delegate to `self.toggle_connection()`.
2. **`pypost/ui/presenters/tabs_presenter_hotkeys.py`**:
   - Rename `handle_websocket_connect_global` to `handle_websocket_connect_toggle`.
   - Update it to call `ws_tab.presenter.toggle_connection()`.
   - Rename `handle_mcp_client_connect_global` to `handle_mcp_client_connect_toggle`.
   - Provide aliases for backward compatibility:
     `handle_websocket_connect_global = handle_websocket_connect_toggle`
     `handle_mcp_client_connect_global = handle_mcp_client_connect_toggle`
   - Update `_F5_ROUTES` mapping.
3. **`tests/test_main_window_hotkeys.py`**:
   - Update `test_f5_on_websocket_tab_toggles_connect`, `_spy_idle`, and
     `test_websocket_routes_logged_per_key` to spy/mock `toggle_connection`.
4. **Verification**:
   - Run `make test` for affected test suites.

## Architecture

```
       F5 Pressed / Global Hotkey
                   │
                   ▼
       handle_f5_global(presenter)
                   │
         _F5_ROUTES lookup
         ┌─────────┴─────────┐
         ▼                   ▼
    [WEBSOCKET]         [MCP_CLIENT]
         │                   │
         ▼                   ▼
handle_websocket_    handle_mcp_client_
 connect_toggle()     connect_toggle()
         │                   │
         ▼                   ▼
ws_tab.presenter.    mcp_tab.presenter.
toggle_connection()  (connect_requested /
         │            disconnect_requested)
         ▼
(handle_disconnect /
 handle_connect)
```

## Q&A

- Q: Does changing `_F5_ROUTES` change any logged action names?
  A: No. The action string in `_F5_ROUTES` is already `"connect_toggle"`, matching the logging
  contract `hotkey_routed key=f5 tab_kind=websocket action=connect_toggle`.
- Q: What happens to `tab.connect_btn.clicked`?
  A: It still connects to `self._on_connect_clicked`, which calls `self.toggle_connection()`.
