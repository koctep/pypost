# PYPOST-135: Dev Docs

## Status

No `doc/dev/` edits required. Existing documentation already covers MCP tool arguments.

## Verified documentation

| Document | Relevant sections |
| --- | --- |
| `doc/dev/mcp_integration.md` | Tool metadata (PYPOST-553), schema generation, variable dict shape, `_merge_execution_variables`, tool execution flow |
| `doc/dev/mcp_secrets_policy.md` | `{{ mcp.request.* }}` vs env-only placeholders, agent schema filtering |

## Key references for maintainers

- Placeholder syntax: `{{ mcp.request.VAR_NAME }}` in URL, headers, params, body
- Model: `McpToolParam`, `RequestData.mcp_params`, `RequestData.mcp_description`
- Schema: `pypost/core/mcp_tool_contract.py` + `MCPServerImpl._generate_schema`
- Execution: `MCPServerImpl._build_execution_variables` → `RequestService.execute`

## Verification

Documentation matches current code paths reviewed for PYPOST-135 closure.
