# PYPOST-81: Observability

## Impact

None. Logger name (`pypost.core.mcp_server_impl`) and log level behaviour are unchanged.

## Existing touchpoints (unchanged)

- `logger.debug` in `MCPServerImpl.__init__` for `TemplateService` injection path.
- MCP metrics and activity logging elsewhere in the module.

## Action

No new logs, metrics, or alerts required for this style-only task.
