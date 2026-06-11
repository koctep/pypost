# PYPOST-557: Observability

## Existing coverage (unchanged)

- `track_mcp_request_received(method)` on each `call_tool`.
- `track_mcp_response_sent(method, outcome)` on completion.

## Change

`track_mcp_response_sent` outcome now reflects the structured **`error` flag** semantics:

| Outcome | When |
| --- | --- |
| `success` | HTTP dispatch completed (`error: false` in envelope) |
| `error` | PyPost execution failed (`execution_error` or `status == 0`) |

Upstream HTTP 4xx/5xx counts as `success` at the MCP metrics layer (execution succeeded).

## Logging

No new log lines. Structured JSON envelope is agent-facing only; avoids logging response bodies.

## Tests

- `test_call_tool_invokes_request_service_with_mcp_context` — metrics `success`
- `test_call_tool_returns_structured_json_with_script_logs_and_error` — implicit error path
- `test_call_tool_upstream_http_error_is_not_execution_error` — metrics would be success
