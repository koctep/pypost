# PYPOST-1102 Observability

## Shared lifecycle

`_dispatch_proxy_operation` now owns the common observability boundary for
`list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `list_resources`, and
`read_resource`.

- One `mcp_requests_received_total` event is recorded per forwarded operation.
- One `mcp_responses_sent_total` event is recorded for success or error.
- Tool calls retain `mcp_tool_call_duration_seconds` with their outcome.
- One bounded activity entry records operation, outcome, duration, and safe
  operation metadata.
- Success and failure logs retain operation-specific event names and durations.

## Safety

Failure activity details use fixed categories rather than exception payloads.
Successful call-tool entries sanitize configured headers before recording them.
Resolved header values, tool arguments, upstream URLs, and raw exception text are
not copied into the new lifecycle records.

## Verification

`tests/test_mcp_proxy_dispatch_repro.py` verifies one request/response lifecycle
for each operation and one tool-duration observation for the tool call. Existing
proxy tests continue to verify masked activity details and timeout, connection,
and unresolved-variable behavior.
