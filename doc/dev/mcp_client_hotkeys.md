# MCP Client session hotkeys (PYPOST-1175 / MCP-TM-9)

Context-aware keyboard shortcuts when an **MCP Client** workspace tab is active.

## Routing

Global shortcuts registered on `MainWindow` delegate to
`TabsPresenter` → `tabs_presenter_hotkeys.py`. Session help rows live in
`main_window_protocol_hotkeys.py`:

| User action | Keys | Handler |
| --- | --- | --- |
| Connect / Disconnect | `F5`, `Ctrl+Return` | `handle_mcp_client_send_global` when MCP tab (invoke-form-unfocused → connect toggle) via Request Editor binding |
| Invoke tool | `Ctrl+Return` | `handle_mcp_client_send_global` when invoke form focused |
| Focus URL | `Ctrl+L`, `Alt+D` | `handle_focus_url` |
| Save / Save As | `Ctrl+S`, `Ctrl+Shift+S` | `McpClientTab` actions (PYPOST-1172) |

Request-editor shortcuts (`Ctrl+P/H/B/T`) no-op when the active tab is not
`RequestTab`.

## Help dialog

- `hotkeys.SECTION_ORDER` includes **MCP Client** after WebSocket Session.
- Connect, Invoke, and Focus URL appear as documentation-only rows
  (`register_hotkey_documentation`) to avoid duplicate Qt shortcut bindings.
- Save rows are tagged on each `McpClientTab` widget.

## API

```python
# pypost/ui/presenters/tabs_presenter_hotkeys.py
def current_mcp_client_tab(presenter: TabsPresenter) -> McpClientTab | None: ...
def handle_mcp_client_connect_global(presenter: TabsPresenter) -> None: ...
def handle_mcp_client_invoke_global(presenter: TabsPresenter) -> None: ...
def handle_mcp_client_send_global(presenter: TabsPresenter) -> None: ...
```

## Tests

```bash
make test PYTEST_ARGS='tests/test_main_window_hotkeys.py::TestMainWindowMcpClientHotkeys -v'
```

## Related

- [mcp_client_collections.md](mcp_client_collections.md) — Save shortcuts
- [websocket_hotkeys.md](websocket_hotkeys.md) — WebSocket peer pattern (PYPOST-1162)
- [doc/user/hotkeys.md](../user/hotkeys.md) — user-facing tables
