# PYPOST-1172: Architecture — Collections save/open + context menu parity

Parent: [`ai-tasks/PYPOST-1164/20-architecture.md`](../PYPOST-1164/20-architecture.md) (MCP-TM-7).

## Module touch list

| Module | Change |
| --- | --- |
| `pypost/models/models.py` | `Collection.mcp_clients: List[McpClientConnection]` |
| `pypost/core/mcp_client_registry.py` | Index, save, delete, rename, find_item |
| `pypost/core/mcp_client_persisted_fields.py` | Snapshot / dirty helpers |
| `pypost/ui/mcp_client_save_orchestrator.py` | Save / Save As (mirror WS orchestrator) |
| `pypost/ui/presenters/collection_tree_actions.py` | Resolve `mcp_client`, context menu |
| `pypost/ui/presenters/collections_presenter.py` | Tree rows, signals, sidebar open |
| `pypost/ui/presenters/tabs_presenter.py` | Save handlers, restore, isolated open |
| `pypost/ui/main_window_signals.py` | Wire collections ↔ tabs signals |
| `pypost/ui/widgets/mcp_client/mcp_client_tab.py` | Save / Save As actions |

## Failing repro (Step 3)

| Test | Intended failure before fix |
| --- | --- |
| `test_save_draft_to_collection` | No orchestrator / no `mcp_clients[]` persistence |
| `test_mcp_client_new_tab_emits_isolated_open_with_protocol_metric` | `_resolve_item_target` missing |
| `test_resolve_item_target_returns_mcp_client` | Tree could not resolve MCP Client rows |

## Restore flow

`restore_tabs` checks `McpClientRegistry.find_item(id)` after WebSocket registry lookup;
saved profile ids in `StateManager.open_tabs` reopen via `open_mcp_client_tab`.
