# PYPOST-181: Observability (Step 5)

## Scope

No new metrics or log statements. Integration tests exercise existing `MCPServerImpl`
`list_tools` / `call_tool` paths with mocked `RequestService`; production observability
signals are unchanged.

## Existing signals (referenced)

| Signal | Location | Relation to this task |
| --- | --- | --- |
| `mcp_requests_received_total` | Prometheus :9080 | Emitted on real app tool calls; not started in these tests |
| `McpActivityLog` | `mcp_activity_log.py` | Optional injection; not wired in test harness |
| Integration harness | `test_mcp_server_integration.py` | Same live protocol pattern; synthetic tools |

## Operator guidance

Collection integration tests do not start the full PyPost app. Manual verification with
real SSE probes remains in `config/test/README.md`.
