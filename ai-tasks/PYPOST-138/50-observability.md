# PYPOST-138: Observability

## New logging

| Location | Message | Level |
| --- | --- | --- |
| `MCPServerImpl._create_request_service` | `creating RequestService for MCP call` | DEBUG |

## Rationale

Confirms per-invocation service creation during troubleshooting without logging secrets or
per-request HTTP details. Volume is bounded by MCP call rate.

## Metrics

No new metrics. Existing MCP counters (`track_mcp_request_received`, duration, outcome)
unchanged.
