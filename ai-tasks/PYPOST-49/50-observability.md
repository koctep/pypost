# PYPOST-49: Observability Implementation

## Logging Implementation

No new logs added. Existing metrics server lifecycle logs preserved in `MetricsServer`:

- **INFO:** `Metrics server starting on %s:%d`
- **INFO:** `metrics_server_listening host=%s port=%d`
- **ERROR:** `metrics_server_start_failed host=%s port=%d message=%s`
- **WARNING:** `metrics_server_unexpected_exit`

## Metrics Implementation

No new metrics. Split preserves all existing Prometheus counters and MCP observability counters
(`mcp_requests_received_total`, `mcp_responses_sent_total`, etc.).

### Module ownership after split

| Concern | Owner |
| --- | --- |
| Counter registration and `track_*` | `MetricsRegistry` |
| MCP scrape side effects on `read_resource` | `MetricsServer` (via registry) |
| HTTP `/metrics` scrape | `MetricsServer._create_app()` |

## Monitoring Integration

- [x] Prometheus metrics — unchanged routes and names
- [ ] Grafana dashboards — N/A for structural refactor
- [ ] Alerting rules — N/A
- [x] Log aggregation — uses existing application logging

## Validation Results

- [x] Scrape output unchanged (unit tests assert counter text)
- [x] MCP resource URI `metrics://all` unchanged
- [x] Bind failure signaling via `MetricsManager.start_failed` unchanged

## Notes

Observability behavior is unchanged; the split improves test isolation without altering
production telemetry.
