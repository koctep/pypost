# MCP Client collections (PYPOST-1172)

Saved outbound MCP Client profiles live on `Collection.mcp_clients[]` as `McpClientConnection`
records (URL, headers, optional `last_tool_name` / `last_tool_arguments`).

## Save flow

`McpClientTab` Actions → Save / Save As emits through `TabsPresenter` into
`McpClientSaveOrchestrator`, which persists via `McpClientRegistry.save_mcp_client` (mirror of
WebSocket save).

## Collections tree

- Row label: `mcp {name}`
- Click: `open_mcp_client_tab` (dedupe by profile id)
- Context menu: New tab (isolated copy), Rename, Delete

## Session restore

Saved profile ids are included in `StateManager.open_tabs`; unsaved drafts are omitted.
`restore_tabs` resolves ids through `McpClientRegistry.find_item`.

## Tests

- `tests/test_mcp_client_save_orchestrator.py`
- `tests/test_collection_tree_actions.py::TestCollectionTreeActionsMcpClient`

See also [`mcp_client_draft_tab.md`](mcp_client_draft_tab.md).
