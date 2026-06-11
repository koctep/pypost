# PYPOST-551: Observability (Step 5)

## Existing instrumentation (unchanged)

- `MCPServerImpl._build_execution_variables` — DEBUG `mcp_execution_variables_merged`
- `MCPClientService` — DEBUG start/success, ERROR on failure with `url` and `operation`
- `MetricsManager` MCP resource handlers — existing `track_mcp_request_received` /
  `track_mcp_response_sent` on `read_resource:metrics`

## Transport migration impact

- No new metrics added; transport change does not alter tool execution paths or counters.
- Connection URL in logs now reflects Streamable HTTP (`/mcp`) when clients use the new path.
- SDK `StreamableHTTPSessionManager` emits INFO on session create/destroy (SDK default logging).

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: (subagent aggregate)
