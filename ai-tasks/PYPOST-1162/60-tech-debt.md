# PYPOST-1162: Technical Debt

## Non-blockers

| Item | Priority | Notes |
| --- | --- | --- |
| **Save rows only when WS tab open** | Low | Help → Hotkeys lists WebSocket Save/Save As only when a `WebSocketTab` exists in the widget tree (`findChildren`). Same pattern as HTTP save on `RequestEditor`. |
| **MCP Client hotkey section** | Medium | `active_tab_kind()` returns `MCP_CLIENT` but no MCP Session shortcuts registered — tracked in PYPOST-1175. |
| **Clear Stream shortcut** | Low | Documented in some epic notes but not in Jira WS-TM-6 acceptance criteria; defer. |
| **Composer send when disconnected** | Low | Send shortcut no-ops with existing `composer_send_blocked_not_open` log; acceptable. |

## Blockers

None — safe to close.

## Follow-ups

| Summary | Priority | Jira |
| --- | --- | --- |
| MCP Client context-aware shortcuts | Medium | [PYPOST-1175](https://pypost.atlassian.net/browse/PYPOST-1175) |

Note: MCP follow-up may already exist as PYPOST-1175 per PYPOST-1164 roadmap.
