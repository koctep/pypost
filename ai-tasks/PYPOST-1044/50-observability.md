# PYPOST-1044: Observability Implementation

## Logging Implementation

### Added Logs

- **ERR**: `MCPServerManager` already reports startup/bind failures with host,
  port, and an operator-facing reason. The registry preserves that failure on
  the affected instance only.
- **WARNING**: `MCPServerRegistry._rollback_reconfiguration` reports a failed
  replacement and rollback using instance ID, attempted port, and failure
  reason.
- **INFO**: `MCPServerRegistry.start()` and `.stop()` log the requested
  lifecycle action with the stable instance ID and port. `_set_status()` logs
  the resulting lifecycle state and whether an operator message exists.

The logs deliberately omit collection names, environment names, request data,
environment variables, hidden-key values, credentials, and full error payloads.
They use key/value fields (`instance_id`, `port`, `state`, and
`message_present`) so an operator can correlate endpoint lifecycle without
exposing endpoint configuration content.

### Log Structure

- Structured logs: yes (stable key/value fields)
- Includes context: yes (instance identity, port, lifecycle state)
- Log levels: ERROR, WARNING, INFO

## Metrics Implementation

### System Health Metrics

- **`mcp_server_instances{state}`**: aggregate configured MCP endpoints in
  `stopped`, `starting`, `running`, or `failed` state. It is published by the
  registry whenever configuration or lifecycle state changes.
- **`mcp_server_up`**: existing compatibility gauge now remains `1` while at
  least one registry endpoint is running; it is not reset when a different
  instance stops or fails.

The only metric label is the fixed, four-value lifecycle `state`; no instance
ID, port, collection, environment, URL, or secret becomes a metric label.
Prometheus and OpenTelemetry trackers expose the same metric shape.

## Monitoring Integration

- [x] Prometheus metrics
- [x] OpenTelemetry metrics
- [ ] Grafana dashboards (out of scope)
- [ ] Alerting rules (out of scope)
- [ ] Log aggregation (deployment-owned)

## Validation Results

- [x] Logs are correctly formatted and contain no large data structures.
- [x] Metrics are collected correctly by Prometheus and OpenTelemetry tests.
- [x] Failed-instance state is represented independently of running instances.
- [x] The asynchronous bind-failure signal cannot be overwritten by the
  following legacy stopped signal before metrics are scraped.
- [x] Lifecycle logs cover start, stop, rollback, and bind-failure paths.
- [x] Metric labels contain no user-controlled identity or secrets.

## Notes

Per-request MCP counters and duration histograms remain shared across all MCP
endpoints. Per-instance activity remains in each manager's activity log;
adding server IDs to request metric labels would create unnecessary cardinality
and could disclose user configuration, so it is intentionally avoided.
