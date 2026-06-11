# PYPOST-141: Observability

## Logging

| Location | Level | Message key | Fields |
| --- | --- | --- | --- |
| `mcp_activity_log.py` `append` | INFO | `mcp_activity_recorded` | operation, outcome, tool_name, tool_count, mcp_arg_count, http_status, duration_ms |
| `mcp_activity_log.py` `clear` | INFO | `mcp_activity_cleared` | count |
| `env_presenter.py` | INFO | `mcp_activity_dialog_opened` | entry_count |

Existing DEBUG `mcp_execution_variables_merged` in `MCPServerImpl` unchanged.

## Metrics

No new Prometheus counters — MCP request/response metrics already tracked via
`MetricsManager.track_mcp_request_received` / `track_mcp_response_sent`.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 1200
