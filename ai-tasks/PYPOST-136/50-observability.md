# PYPOST-136: Observability

## Logging

| Event | Level | Message |
| --- | --- | --- |
| Exposed tool set changed while running | INFO | `mcp_tools_changed tool_count=N restarting=true` |

Existing startup/stop logs (`mcp_server_listening`, `mcp_server_stopped`) cover the restart
tail of the refresh flow.

## Metrics

No new Prometheus counters — `MCPServerImpl.register_tools` already updates
`mcp_server_up` gauge on restart via existing metrics hook.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 700
