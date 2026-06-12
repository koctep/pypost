# PYPOST-166: Observability

## Impact

Routing change (PYPOST-75) did not alter observability behavior:

| Surface | Unchanged |
| --- | --- |
| HTTP GET `/metrics` | Prometheus text scrape |
| MCP `metrics://all` | Same resource URI and counters |
| `mcp_*_total` counters | Still incremented on MCP resource read |
| Default port | 9080 (settings) |

## Verification

- `TestMetricsServerAsgiCompatibility.test_metrics_mount_serves_prometheus_via_asgi` —
  mount serves scrape with registered counters.
- `tests/test_metrics_server_endpoint.py` — HTTP `/metrics` 200 and counter text.

No new logging or metrics added for this debt closure.
