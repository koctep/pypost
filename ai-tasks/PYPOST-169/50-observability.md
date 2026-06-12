# PYPOST-169: Observability

Tests-only task; no new logging or metrics in production code.

| Signal | Coverage |
| --- | --- |
| HTTP GET `/metrics` | `TestMetricsServerHttpIntegration` — live scrape after uvicorn start |
| MCP `metrics://all` | Existing `TestMetricsServerMcpIntegration` (PYPOST-563) |

Existing tests:

- `tests/test_metrics_server_endpoint.py` — ASGI unit scrape
- `tests/test_metrics_server_startup.py` — bind / listen signaling

No additional instrumentation required.
