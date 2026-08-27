# PYPOST-1175: Architecture — Context-aware MCP Client shortcuts

## Overview

Extend `tabs_presenter_hotkeys.py` (from PYPOST-1162) with MCP Client routing.
`main_window._setup_shortcuts` registers **MCP Client** documentation rows;
`hotkeys.SECTION_ORDER` adds the section after WebSocket Session.

## Components

| Module | Change |
| --- | --- |
| `tabs_presenter_hotkeys.py` | `current_mcp_client_tab`, MCP connect/invoke/send handlers, focus URL branch |
| `tabs_presenter.py` | Thin delegates on new `handle_mcp_client_*_global` methods |
| `main_window_protocol_hotkeys.py` (new) | WS/MCP session help rows + WS Format JSON |
| `main_window.py` | Calls `register_protocol_session_hotkeys` |
| `hotkeys.py` | `SECTION_ORDER` += `"MCP Client"` |
| `mcp_client_tab.py` | Wire Ctrl+S/Ctrl+Shift+S actions; expose `invoke_form` property |

## Routing rules

| Shortcut | MCP Client tab active | Request tab active |
| --- | --- | --- |
| F5 / Ctrl+Return (global Send slot) | Connect/Disconnect toggle; Invoke when invoke form focused | Send request |
| Ctrl+L / Alt+D | Focus MCP URL bar | Focus request URL |
| Ctrl+P/H/B/T | No-op | Switch detail tab |
| Ctrl+S / Ctrl+Shift+S | `McpClientTab` actions | Request editor actions |

## Red tests (Step 3)

| Test | Asserts |
| --- | --- |
| `test_section_order_includes_mcp_client` | `SECTION_ORDER` contains MCP Client |
| `test_mcp_client_tab_ctrl_s_dispatches_save` | Ctrl+S reaches presenter save handler |
| `test_f5_on_mcp_client_tab_toggles_connect` | F5 calls presenter connect path |
| `test_ctrl_l_focuses_mcp_client_url_when_mcp_tab_active` | Focus URL targets MCP editor |
| `test_request_editor_shortcuts_noop_on_mcp_client_tab` | Params switch does not touch request tab |
| `test_invoke_global_dispatches_presenter` | Invoke handler calls presenter invoke path |

## References

- `ai-tasks/PYPOST-1162/20-architecture.md` — WebSocket peer pattern
- `ai-tasks/PYPOST-1172/20-architecture.md` — MCP save orchestrator
