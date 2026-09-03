# PYPOST-1105 Observability

The tests intentionally keep process output at Uvicorn warning level and make
no assertions against raw network logs. Their observable contract is the
downstream MCP result:

- Streamable HTTP returns the complete large payload with both boundary markers.
- Legacy SSE returns the same deterministic tool payload through the proxy.
- Tool discovery returns the expected upstream tool name in both cases.
- Startup, socket readiness, and child teardown have bounded failure paths.

The test harness does not add metrics or application logging. This keeps the
coverage focused on wire transport behavior and avoids making payload content a
production telemetry field.
