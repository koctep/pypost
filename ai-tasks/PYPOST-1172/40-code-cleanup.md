# PYPOST-1172: Code cleanup

- Mirrored WebSocket save/registry patterns without abstracting shared base classes (consistent with WS-TM-5/1160).
- Reused `prompt_deleted_websocket_profile_tab_close` for MCP Client tab close on delete (same UX contract).
- Incremental tree refresh generalized to ordered child list (requests, websockets, mcp_clients).

No further cleanup required in scope.
