# PYPOST-553: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| [doc/dev/mcp_integration.md](../../doc/dev/mcp_integration.md) | Tool metadata model, schema generation, MCP tab |

## Developer notes

- Schema helpers: `_tool_description`, `_resolve_mcp_param_specs`, `_build_tool_input_schema`
  in `pypost/core/mcp_server_impl.py`.
- Model: `McpToolParam`, `RequestData.mcp_description`, `RequestData.mcp_params`.
- UI: **MCP** tab on `RequestWidget` (`McpParamsTable`).

## Cross-references

- Parent epic: PYPOST-549 (tool contract).
- Related: PYPOST-555 (operator preview).
