# PYPOST-1172: Observability

Existing MCP Client presenter metrics unchanged. New log tokens follow registry/orchestrator naming:

- `mcp_client_registry_index_rebuilt`
- `save_mcp_client_started` / `save_mcp_client_succeeded`
- `mcp_client_save_as_flow_*`
- `collection_mcp_client_opened` / `collection_mcp_client_open_new_tab`
- `mcp_client_saved_tab_persisted_in_open_tabs` / `mcp_client_draft_omitted_from_open_tabs`

Save actions use existing `track_gui_save_action` / `track_gui_save_as_action`.
