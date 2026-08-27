# PYPOST-1175: Technical Debt

## Non-blockers (deferred)

| Item | Priority | Notes |
| --- | --- | --- |
| **Disconnect via F5 when CONNECTING** | Low | Toggle calls `disconnect_requested` during CONNECTING; same as WebSocket connect-cancel semantics. |
| **Headers table shortcuts** | Low | No dedicated hotkeys for MCP headers table; out of Jira scope. |
| **Shared tab-kind hotkey test harness** | Low | WS and MCP test classes duplicate presenter setup; extract helper if a third protocol tab adds shortcuts. |

## Resolved in this task

| Item | Was | Resolution |
| --- | --- | --- |
| MCP Client hotkey section missing | `SECTION_ORDER` had no MCP Client | Added section + routing |
| Save shortcuts not bound on MCP tab | `tag_action` only | Wired QAction shortcuts like WebSocket |

No Jira follow-ups required — all items are low-priority deferred work.
