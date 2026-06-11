# PYPOST-155: Observability

## Assessment

No logging or metrics changes required. HTTP 405 responses for wrong methods are still produced
by Starlette routing; MCP request metrics are unchanged (legacy SSE path only).

## Verification

`test_routing_rejects_wrong_http_methods_without_live_transport` confirms 405 on disallowed
methods without starting live SSE transport.
