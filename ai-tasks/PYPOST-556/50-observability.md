# PYPOST-556: Observability

## Logging

| Event | Level | Fields |
| --- | --- | --- |
| MCP server starting | INFO | host, port (existing) |
| MCP listening | INFO | `mcp_server_listening` host, port |
| MCP start failed | ERROR | `mcp_server_start_failed` host, port, message |
| MCP unexpected exit | WARNING | `mcp_server_unexpected_exit` |
| Overview opened | INFO | `mcp_tools_overview_opened` tool_count |
| Overview collected | DEBUG | `mcp_tools_overview_collected` tool_count |
| UI start failure | ERROR | `mcp_server_start_failed_ui` message |

## Metrics

No new Prometheus counters — existing `mcp_requests_received` / `mcp_responses_sent` unchanged.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 900
