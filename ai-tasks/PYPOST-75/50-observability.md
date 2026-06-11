# PYPOST-75: Observability

## Summary

Structural refactor only — no new metrics, logs, or changed counter semantics.

## Existing observability preserved

| Surface | Owner after split | Notes |
| --- | --- | --- |
| Prometheus counters | `MetricsRegistry` | Same names/labels; `registry` exposed via facade |
| MCP `metrics://all` | `MetricsServer` | Still tracks `mcp_requests_received_total` / `mcp_responses_sent_total` |
| Server lifecycle logs | `MetricsServer` | `Metrics server started/stopped` INFO unchanged |
| HTTP routes | `MetricsServer._create_app` | `/metrics`, `/mcp`, `/sse`, `/messages` unchanged |

## Verification

- `tests/test_metrics_manager.py::TestMetricsManagerMcpResource` — MCP resource scrape + counters
- Storage/adapter metrics tests — encryption counter paths through facade

## Gaps

None introduced. Live uvicorn round-trip remains out of scope (pre-existing).
