# WebSocket session hotkeys (PYPOST-1162 / WS-TM-6)

Context-aware keyboard shortcuts when a **WebSocket** workspace tab is active.

## Routing

Global shortcuts registered on `MainWindow` delegate to
`TabsPresenter` → `tabs_presenter_hotkeys.py`:

| User action | Keys | Handler |
| --- | --- | --- |
| Connect / Disconnect | `F5`, `Ctrl+Return` | `handle_websocket_send_global` when WS tab (composer-unfocused → connect) via Request Editor binding |
| Send message | `Ctrl+Return` | `handle_websocket_send_global` when composer focused |
| Focus URL | `Ctrl+L`, `Alt+D` | `handle_focus_url` |
| Format JSON | `Ctrl+Shift+F` | `handle_websocket_format_json_global` → `WebSocketComposer.format_json_payload` |
| Save / Save As | `Ctrl+S`, `Ctrl+Shift+S` | `WebSocketTab` actions (PYPOST-1161) |

Request-editor shortcuts (`Ctrl+P/H/B/T`) no-op when the active tab is not
`RequestTab`.

## Help dialog

- `hotkeys.SECTION_ORDER` includes **WebSocket Session** after Request Editor.
- Connect, Send, and Focus URL appear as documentation-only rows
  (`register_hotkey_documentation`) to avoid duplicate Qt shortcut bindings.
- Save rows are tagged on each `WebSocketTab` widget.

## API

```python
# pypost/ui/presenters/tabs_presenter_hotkeys.py
def active_tab_kind(presenter: TabsPresenter) -> TabProtocol | None: ...
def handle_websocket_connect_global(presenter: TabsPresenter) -> None: ...
def handle_websocket_send_global(presenter: TabsPresenter) -> None: ...
```

## Tests

```bash
make test PYTEST_ARGS='tests/test_main_window_hotkeys.py -v'
```

## Related

- [websocket_save_flow.md](websocket_save_flow.md) — Save shortcuts
- [doc/user/hotkeys.md](../user/hotkeys.md) — user-facing tables
