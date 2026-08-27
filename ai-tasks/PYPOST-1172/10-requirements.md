# PYPOST-1172: MCP-TM-7 — Collections save/open + context menu parity

## Goals

Persist MCP Client profiles in collections (`mcp_clients[]`), Save/Save As from workspace tabs,
sidebar open/focus, context menu New tab / Rename / Delete parity, and session restore for saved
profiles.

Parent architecture: [`ai-tasks/PYPOST-1164/20-architecture.md`](../PYPOST-1164/20-architecture.md)
(MCP-TM-7). Depends on MCP-TM-2 blank MCP Client tab shell (PYPOST-1166).

## Acceptance criteria (from Jira)

- [x] `mcp_clients[]` field in collection JSON
- [x] `McpClientSaveOrchestrator` for Save / Save As
- [x] `collection_tree_actions` resolves `McpClientConnection`
- [x] Sidebar open creates/focuses MCP Client tab
- [x] Context menu New tab / Rename / Delete; delete closes open tabs
- [x] `restore_tabs` opens saved MCP Client profiles by id

## Functional requirements

- FR-1: Save draft MCP Client tab to collection (Save / Save As dialogs mirror WebSocket).
- FR-2: Saved profiles appear in collections tree as `mcp {name}` rows.
- FR-3: Single-click sidebar open deduplicates by profile id (focus existing tab).
- FR-4: Context **New tab** opens isolated copy with `protocol=mcp_client` metric.
- FR-5: Rename / Delete dispatch via collection item strategies; delete emits tab-close signal.
- FR-6: Unsaved drafts omitted from `save_tabs_state`; saved profile ids restored on startup.

## References

- PYPOST-1160 WebSocket collections parity (pattern)
- PYPOST-1161 WebSocket save orchestrator (pattern)
