# PYPOST-1162: Architecture — Context-aware WebSocket shortcuts

## Overview

Extract tab-kind hotkey routing to `tabs_presenter_hotkeys.py` (keeps
`tabs_presenter.py` under LOC cap). `main_window._setup_shortcuts` registers
**WebSocket Session** globals; `hotkeys.SECTION_ORDER` adds the section between
Request Editor and ad-hoc sections.

## Components

| Module | Change |
| --- | --- |
| `tabs_presenter_hotkeys.py` (new) | `active_tab_kind`, WS/request tab getters, routed handlers |
| `tabs_presenter.py` | Thin delegates on existing `handle_*_global` methods |
| `main_window.py` | Register WS Session: Connect, Send, Focus URL, Format JSON |
| `hotkeys.py` | `SECTION_ORDER` += `"WebSocket Session"` |
| `composer.py` | `format_json_payload()` for Ctrl+Shift+F |

## Routing rules

| Shortcut | WS tab active | Request tab active |
| --- | --- | --- |
| F5 / Ctrl+Return (global Send slot) | Connect/Disconnect toggle | Send request |
| Ctrl+Return (WS Send slot) | Send when composer focused, else connect | N/A (not registered) |
| Ctrl+L / Alt+D | Focus WS URL bar | Focus request URL |
| Ctrl+P/H/B/T | No-op | Switch detail tab |
| Ctrl+S / Ctrl+Shift+S | `WebSocketTab` actions (unchanged) | Request editor actions |

## Red tests (Step 3)

| Test | Asserts |
| --- | --- |
| `test_websocket_tab_ctrl_s_dispatches_save` | Ctrl+S reaches presenter save handler |
| `test_f5_on_websocket_tab_toggles_connect` | F5 calls presenter connect path |
| `test_ctrl_l_focuses_websocket_url_when_ws_tab_active` | Focus URL targets WS editor |
| `test_request_editor_shortcuts_noop_on_websocket_tab` | Params switch does not touch request tab |
| `test_section_order_includes_websocket_session` | `SECTION_ORDER` contains WebSocket Session |

## References

- `ai-tasks/PYPOST-1156/20-architecture.md` — WS-TM-6 acceptance criteria
- `ai-tasks/PYPOST-1161/20-architecture.md` — save shortcut split
