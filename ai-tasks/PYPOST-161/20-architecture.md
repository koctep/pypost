# PYPOST-161: ASGI compatibility test architecture

## Research

- Starlette `Route` wraps non-ASGI endpoints in `request_response`, which expects a `Response`
  return value. Low-level MCP transports (`handle_post_message`, Streamable HTTP session
  manager) return `None` and write via ASGI `send`.
- Module-level `MessagesEndpoint` and `StreamableHTTPASGIApp` are recognized as ASGI when
  registered on `Route`; `route.app` remains the endpoint instance (not a `request_response`
  closure).
- `MetricsServer._create_app()` mounts Prometheus via `Mount("/metrics")`, registers
  Streamable HTTP on `Route("/mcp")`, and legacy SSE via `Mount("/sse")`.
- PYPOST-158 covers SSE close contract and 405 guards; this task adds ASGI registration checks.

## Implementation Plan

1. Add `tests/test_mcp_asgi_compatibility.py` with helper `_assert_route_uses_direct_asgi`.
2. Legacy SSE: assert `MessagesEndpoint` on inner `/messages` route; mock `handle_post_message`
   and assert POST completes without `TypeError`.
3. Streamable HTTP: assert `/mcp` route on `MCPServerImpl` and `MetricsServer` apps.
4. Metrics server: assert `/metrics` mount, `/mcp` route, `/sse` mount; scrape `/metrics`.
5. Update `doc/dev/testing.md` MCP server unit test table.

## Test layout

```text
tests/test_mcp_asgi_compatibility.py
├── TestLegacySseAsgiCompatibility
├── TestStreamableHttpAsgiCompatibility
├── TestMetricsServerAsgiCompatibility
└── TestMcpServerAsgiCompatibility
```

## Q&A

- **Q:** Why inspect `route.app` type instead of calling Starlette internals?
  - **A:** When wrapped, `route.app` is a `request_response` closure function; direct ASGI keeps
    the endpoint instance type — a stable public regression signal.
