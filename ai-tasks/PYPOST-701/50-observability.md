# PYPOST-701: Observability

## Scope

No observability changes — documentation-only task.

## Existing coverage (unchanged)

- **GUI history:** `RequestService._record_execution_history()` with masking metrics and debug
  logs (PYPOST-463).
- **Inbound MCP activity:** Session-scoped `McpActivityDialog` records `list_tools` /
  `call_tool` operations (PYPOST-141) — separate from persistent request history.
- **Inbound MCP execution:** DEBUG `mcp_execution_variables_merged` in
  `MCPServerImpl._build_execution_variables` (PYPOST-554).

Documentation now clarifies that MCP activity log is not a substitute for request history.
