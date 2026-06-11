# PYPOST-154: Observability

## Verification

Both servers already log bind failures at ERROR with host, port, and message:

| Server | Log key | UI log key |
| --- | --- | --- |
| MCP | `mcp_server_start_failed` | `mcp_server_start_failed_ui` |
| Metrics | `metrics_server_start_failed` | `metrics_server_start_failed_ui` |

## Metrics

No new Prometheus counters — verification only.
