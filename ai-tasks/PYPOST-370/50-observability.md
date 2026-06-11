# PYPOST-370: Observability

## Summary

Closure task. No new logging or metrics in production code.

## Existing Coverage (unchanged)

| Surface | Test location | Asserted metrics |
| --- | --- | --- |
| MCP tool `call_tool` | `tests/test_mcp_server_impl.py` | `track_mcp_request_received`, `track_mcp_response_sent` (mocked) |
| Metrics `read_resource` | `tests/test_metrics_manager.py` | `mcp_requests_received_total`, `mcp_responses_sent_total` (scraped) |
| Live MCP tool SSE | `tests/test_mcp_server_integration.py` | Execute mocked; no Prometheus scrape |

## Gap (follow-up)

Live metrics server MCP SSE round-trip does not increment counters via a real client session;
unit tests call `MetricsManager.read_resource` directly.
