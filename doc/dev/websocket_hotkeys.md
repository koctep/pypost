# WebSocket session hotkeys (PYPOST-1162 / WS-TM-6)

Keyboard shortcuts when a **WebSocket** workspace tab is active.

## Routing

Global shortcuts registered on `MainWindow` delegate to
`TabsPresenter` → `tabs_presenter_hotkeys.py`. F5 and Ctrl+Return are routed by the active tab
kind only. Keyboard focus does not matter
([PYPOST-1285](https://pypost.atlassian.net/browse/PYPOST-1285)); see
[hotkeys.md](hotkeys.md#send-key-routing-f5--ctrlreturn).

| User action | Keys | Handler |
| --- | --- | --- |
| Connect / Disconnect | `F5` | `handle_f5_global` → `_F5_ROUTES[WEBSOCKET]` → `handle_websocket_connect_toggle` (toggle) |
| Send message | `Ctrl+Return` | `handle_ctrl_return_global` → `_CTRL_RETURN_ROUTES[WEBSOCKET]` → `handle_websocket_send_message_global` |
| Focus URL | `Ctrl+L`, `Alt+D` | `handle_focus_url` |
| Format JSON | `Ctrl+Shift+F` | `handle_websocket_format_json_global` → `WebSocketComposer.format_json_payload` |
| Save / Save As | `Ctrl+S`, `Ctrl+Shift+S` | `WebSocketTab` actions (PYPOST-1161) |

- `F5` toggles the session whether or not the composer has focus. It never sends.
- `Ctrl+Return` sends the composer payload from anywhere in the tab. It never connects or
  disconnects. The presenter's existing guard still applies: sending while the session is not
  `OPEN` is blocked and logs `websocket_send_blocked_not_open`.
- Every routed key logs `hotkey_routed` at DEBUG (see [logging.md](logging.md)).

Request-editor shortcuts (`Ctrl+P/H/B/T`) no-op when the active tab is not
`RequestTab`.

## Help dialog

- `hotkeys.SECTION_ORDER` includes **WebSocket Session** after Request Editor.
- Connect (`F5`), Send (`Ctrl+Return`), and Focus URL appear as documentation-only rows
  (`register_hotkey_documentation` in `main_window_protocol_hotkeys.py`). These rows never bind
  a key. A second binding would make the key ambiguous in Qt and stop it from firing; see
  [hotkeys.md](hotkeys.md#documentation-only-rows-display-never-bind).
- Save rows are tagged on each `WebSocketTab` widget.

## API

```python
# pypost/ui/presenters/tabs_presenter_hotkeys.py
def active_tab_kind(presenter: TabsPresenter) -> TabProtocol | None: ...
def handle_f5_global(presenter: TabsPresenter) -> None: ...
def handle_ctrl_return_global(presenter: TabsPresenter) -> None: ...
# Route handlers: True when the action ran, False when the tab/presenter is missing.
def handle_websocket_connect_toggle(presenter: TabsPresenter) -> bool: ...
def handle_websocket_send_message_global(presenter: TabsPresenter) -> bool: ...
```

`handle_websocket_connect_toggle` invokes `ws_tab.presenter.toggle_connection()`
([PYPOST-1296](https://pypost.atlassian.net/browse/PYPOST-1296)). Backward-compatibility alias
`handle_websocket_connect_global` is retained.


## Tests

```bash
make test PYTEST_ARGS='tests/test_main_window_hotkeys.py -v'
```

`TestCtrlReturnF5RoutingWebSocket` covers both keys with and without composer focus, in
`IDLE` and `OPEN` states.

## Related

- [hotkeys.md](hotkeys.md) — registration helpers, send-key routing, documentation-row rule
- [websocket_save_flow.md](websocket_save_flow.md) — Save shortcuts
- [doc/user/hotkeys.md](../user/hotkeys.md) — user-facing tables
