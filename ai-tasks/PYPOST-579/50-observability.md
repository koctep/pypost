# PYPOST-579: Observability (Step 5)

## Scope

This task **is** observability infrastructure: the adapter records the same application
signals as `MetricsRegistry`, exported via OpenTelemetry instead of Prometheus client.

## Instrument mapping

| Protocol method | OTel instrument | Prometheus equivalent |
| --- | --- | --- |
| `track_*` (most) | Counter | `Counter.inc()` |
| `track_mcp_tool_call_duration` | Histogram (`unit="s"`) | `Histogram.observe()` |
| `set_mcp_server_up` | Observable gauge | `Gauge.set(0\|1)` |

Metric names match `pypost/core/metrics_registry.py` (e.g. `requests_sent_total`,
`mcp_tool_call_duration_seconds`).

## Operator guidance

Configure exporters on the `MeterProvider` before calling `create_otel_metrics_tracker`.
The adapter does not start HTTP servers or scrape endpoints — export is entirely driven by
the provider the operator installs.

## Application logging

No new log statements in the adapter; recording is synchronous and lightweight.
