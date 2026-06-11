# PYPOST-180: Observability (Step 5)

## Scope

No new metrics or log statements. Tests validate committed MCP test data that operators use
for manual verification; observability signals remain unchanged.

## Existing signals (referenced)

| Signal | Location | Relation to this task |
| --- | --- | --- |
| `mcp_requests_received_total` | Prometheus :9080 | Used after manual/agent tool calls per `config/test/README.md` |
| Integration tests | `test_mcp_server_integration.py` | Live protocol coverage; separate from collection validation |
| Doc consistency | `test_mcp_user_docs.py` | Complements collection structure tests |

## Operator guidance

Groundwork tests do not start MCP servers. Manual verification flow unchanged; see
`config/test/README.md` and `doc/dev/testing.md`.
