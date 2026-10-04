# MCP Client session hotkeys (PYPOST-1175 / MCP-TM-9)

Keyboard shortcuts when an **MCP Client** workspace tab is active.

## Routing

Global shortcuts registered on `MainWindow` delegate to
`TabsPresenter` → `tabs_presenter_hotkeys.py`. Session help rows live in
`main_window_protocol_hotkeys.py`. F5 and Ctrl+Return are routed by the active tab kind only.
Keyboard focus does not matter
([PYPOST-1285](https://pypost.atlassian.net/browse/PYPOST-1285)); see
[hotkeys.md](hotkeys.md#send-key-routing-f5--ctrlreturn).

| User action | Keys | Handler |
| --- | --- | --- |
| Connect / Disconnect | `F5` | `handle_f5_global` → `_F5_ROUTES[MCP_CLIENT]` → `handle_mcp_client_connect_global` (toggle by session state) |
| Invoke tool | `Ctrl+Return` | `handle_ctrl_return_global` → `_CTRL_RETURN_ROUTES[MCP_CLIENT]` → `handle_mcp_client_invoke_global` |
| Focus URL | `Ctrl+L`, `Alt+D` | `handle_focus_url` |
| Save / Save As | `Ctrl+S`, `Ctrl+Shift+S` | `McpClientTab` actions (PYPOST-1172) |

- `F5` calls `disconnect_requested()` when the session is connected or connecting, and
  `connect_requested()` otherwise. It does this whether or not the invoke form has focus, and it
  never invokes.
- `Ctrl+Return` calls `invoke_requested()` from anywhere in the tab. It never connects or
  disconnects. The presenter's existing invoke guards are unchanged.
- Every routed key logs `hotkey_routed` at DEBUG (see [logging.md](logging.md)).

Request-editor shortcuts (`Ctrl+P/H/B/T`) no-op when the active tab is not
`RequestTab`.

## Help dialog

- `hotkeys.SECTION_ORDER` includes **MCP Client** after WebSocket Session.
- Connect (`F5`), Invoke (`Ctrl+Return`), and Focus URL appear as documentation-only rows
  (`register_hotkey_documentation`). These rows never bind a key, so the real bindings stay
  unambiguous; see [hotkeys.md](hotkeys.md#documentation-only-rows-display-never-bind).
- Save rows are tagged on each `McpClientTab` widget.

## API

```python
# pypost/ui/presenters/tabs_presenter_hotkeys.py
def current_mcp_client_tab(presenter: TabsPresenter) -> McpClientTab | None: ...
def handle_f5_global(presenter: TabsPresenter) -> None: ...
def handle_ctrl_return_global(presenter: TabsPresenter) -> None: ...
# Route handlers: True when the action ran, False when no MCP tab is active.
def handle_mcp_client_connect_global(presenter: TabsPresenter) -> bool: ...
def handle_mcp_client_invoke_global(presenter: TabsPresenter) -> bool: ...
```

`handle_mcp_client_connect_global` toggles despite its name. A rename is tracked in
[PYPOST-1296](https://pypost.atlassian.net/browse/PYPOST-1296).

## Tests

```bash
make test PYTEST_ARGS='tests/test_main_window_hotkeys.py::TestMainWindowMcpClientHotkeys tests/test_main_window_hotkeys.py::TestCtrlReturnF5RoutingMcpClient -v'
```

## Related

- [hotkeys.md](hotkeys.md) — registration helpers, send-key routing, documentation-row rule
- [mcp_client_collections.md](mcp_client_collections.md) — Save shortcuts
- [websocket_hotkeys.md](websocket_hotkeys.md) — WebSocket peer pattern (PYPOST-1162)
- [doc/user/hotkeys.md](../user/hotkeys.md) — user-facing tables
