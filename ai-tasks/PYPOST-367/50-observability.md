# PYPOST-367: Observability

## Scope

Test-only task. No new logging or metrics in production code.

## Existing Observability Under Test

| Signal | Test coverage |
| --- | --- |
| `track_mcp_request_received` | `test_call_tool_invokes_request_service_with_mcp_context` |
| `track_mcp_response_sent` success | Same test |
| `track_mcp_response_sent` error | `test_call_tool_on_execute_exception_returns_error_content_and_metrics` |

## Notes

Routing tests do not assert log output. SSE lifecycle logging remains covered by manual/MCP
integration flows documented in `doc/dev/testing.md`.
