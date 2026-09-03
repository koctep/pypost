# PYPOST-1100: Observability Implementation

## Logging Implementation

### Added Logs

The validation boundary emits one safe structured warning for each rejected call:

- **WARNING**: `pypost/core/mcp_observability.py` - `mcp_argument_validation_failed`
  with `stage`, `transport`, `tool`, `param`, and `expected_type` fields.
- **EMERG**: None added for expected argument validation failures.
- **ALERT**: None added for expected argument validation failures.
- **CRIT**: None added for expected argument validation failures.
- **ERR**: None added for expected argument validation failures.
- **NOTICE**: None added for expected argument validation failures.
- **INFO**: None added for expected argument validation failures.
- **DEBUG**: None added for expected argument validation failures.

The event contains no received argument values, serialized arguments, defaults,
secrets, or request bodies. The stage is `preflight` for HTTP and WebSocket
application validation and `execution_boundary` for effective HTTP defaults.
Default application INFO logs contain only the method, parameter name,
`default_applied=true`, and the declared default type; the default value is never
serialized.

### Log Structure

Log format used:

- Structured logs: yes, using bounded `key=value` fields.
- Includes context: yes, with transport, stage, tool, parameter, and expected type.
- Log levels: WARNING.

## Metrics Implementation

### Performance Metrics

Added performance metrics:

- **Response time**: `mcp_tool_call_duration_seconds{method,status}` records
  `status="validation_error"` for rejected calls.
- **Throughput**: `mcp_responses_sent_total{method,status}` records one
  `validation_error` response outcome per rejected call.
- **Error rate**: `mcp_argument_validation_failures_total{stage,transport,declared_type}`
  counts rejected declared values with bounded labels.

### Business Metrics

Business metrics:

- None; argument validation is an operational contract outcome.

### System Health Metrics

System health metrics:

- **Resource usage**: None added; existing metrics remain unchanged.
- **Component status**: None added; existing MCP server status metrics remain unchanged.

The new tracker method is implemented by `MetricsTrackerProtocol`, `NullMetrics`,
`MetricsRegistry`, `OtelMetricsTracker`, and the Qt `MetricsTrackingMixin`.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

The existing Prometheus and OpenTelemetry tracker surfaces expose the new counter;
dashboard, alert, and log-aggregation configuration is outside this task.

## Validation Results

Validation results:

- [x] Logs are correctly formatted
- [x] Metrics are collected correctly
- [x] Logging works in error scenarios
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring

Focused command:

```sh
make test \
  PYTEST_ARGS="tests/test_mcp_validation_observability.py tests/test_mcp_tool_contract.py \
  tests/test_mcp_server_impl.py tests/test_mcp_server_integration.py \
  tests/test_websocket_mcp_probe_repro.py tests/test_metrics_registry.py \
  tests/test_metrics_otel.py tests/test_metrics_protocol.py"
```

Result: 8 test files passed, 0 failed, and 0 skipped.

Other required checks:

- `make lint` — passed.
- `make typecheck` — passed; 180 known baseline errors remain.
- `make verify-ai-tasks` — passed; 346 completed tasks and 2 grandfathered gaps.

The full `make test` baseline remains 323 passed, 4 failed, and 5 skipped. The
remaining failures are pre-existing PYPOST-1261 debt: two parser-alignment tests,
the Qt `tests/test_environment_list_widget.py` file-level `-11` crash, the
`template_service.py` SOLID snapshot mismatch, and two template-service alignment
tests.

## Notes

HTTP and WebSocket preflight failures and HTTP execution-boundary failures each
produce exactly one safe activity entry with `outcome="validation_error"`, no HTTP
status, a bounded duration, and the safe named diagnostic. A preflight failure
does not start a probe or HTTP request. The existing WebSocket probe outcomes for
calls that pass validation remain unchanged.
