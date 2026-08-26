# PYPOST-1171: Migrate/remove HTTP method MCP — architecture

Parent: [`ai-tasks/PYPOST-1164/20-architecture.md`](../PYPOST-1164/20-architecture.md) (MCP-TM-6).

## Implementation Plan

1. Add `pypost/core/mcp_client_migration.py` with `request_data_to_mcp_client`.
2. Extend `McpClientConnection` with `last_tool_name` / `last_tool_arguments`.
3. Route `TabsPresenter.add_new_tab` and `open_legacy_mcp_request_tab` for
   `method: "MCP"`.
4. Remove **MCP** from `RequestEditor` method combo and `_execute_mcp` from
   `RequestService`.

## Failing Repro (Step 3)

| Test | Intended failure before fix |
| --- | --- |
| `test_method_combo_excludes_mcp` | Combo still contained **MCP** |
| `test_legacy_mcp_request_opens_client_tab` | Legacy item opened `RequestTab` |

## Module touch list

| Module | Change |
| --- | --- |
| `mcp_client_migration.py` | New adapter |
| `tabs_presenter.py` | `open_legacy_mcp_request_tab`, route in `add_new_tab` |
| `request_editor.py` | Drop **MCP** from combo |
| `request_service.py` | Remove `_execute_mcp` and MCP branch |
| `mcp_client_presenter.py` | Apply pending tool after Connect |
