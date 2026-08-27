# PYPOST-1172: Technical debt

| Item | Priority | Notes |
| --- | --- | --- |
| MCP Client draft dirty-close prompt | Low | WebSocket has `confirm_close_websocket_draft`; MCP draft close still uses generic unsaved prompt only when wired in close path — parity follow-up |
| Collection import `mcp_clients` id collision reservation | Low | Websockets reserve ids on import merge; `mcp_clients` rely on pydantic parse today |
| Dedicated delete-tab dialog copy for MCP Client | Low | Reuses WebSocket delete prompt strings |

No blockers for close.
