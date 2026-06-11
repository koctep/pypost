# PYPOST-552: Observability (Step 5)

## Scope

No new metrics or log statements. Task validates existing MCP observability paths remain
documented for operators.

## Existing signals (unchanged)

| Signal | Location | Use in this task |
| --- | --- | --- |
| `mcp_requests_received_total` | Prometheus :9080 | Checklist optional: confirm counter after call_tool |
| `mcp_operation_*` DEBUG logs | `MCPClientService` | In-app List Tools request troubleshooting |
| Integration tests | `test_mcp_server_integration.py` | Automated list/call verification |

## Operator guidance

Checklist references Prometheus metrics doc in `doc/dev/testing.md` for optional post-call
verification. Not required for Cursor sign-off.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 600
