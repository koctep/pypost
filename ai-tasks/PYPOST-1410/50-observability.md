# PYPOST-1410: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging and diagnostics have been reviewed and enhanced across standalone MCP server execution:

- **WARNING**:
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_runtime_validation_failed` (`category`, `duration_seconds`): Logs validation failure and latency when profile, manifest, or collection validation fails before re-raising `ValueError`.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_missing_required_variables` (`count`, `missing_names`): Emits warning with missing non-secret variable names when required variables are unfulfilled.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_variable_validation_failed` (`error_count`, `errors`): Logs variable type or schema validation errors.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_reconfigure_rolled_back` (`instance_id`, `port`, `reason`): Warns when candidate reconfiguration rolls back to previous configuration.

- **INFO**:
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_runtime_validation_started` (`library_id`, `manifest_id`, `environment_id`): Structured start of runtime validation, explicitly recording `environment_id=None` for standalone servers.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_runtime_validation_completed` (`duration_seconds`, `request_count`, `variable_count`, `environment_id`): Structured completion of runtime validation with duration and payload counts.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_start_requested` (`instance_id`, `port`, `environment_id`, `standalone`): Records server startup requests, explicitly flagging standalone library execution when `environment_id` is None.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_stop_requested` (`instance_id`, `port`): Records endpoint shutdown requests.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_status` (`instance_id`, `state`, `message_present`): Emits lifecycle state transitions (`stopped`, `starting`, `running`, `failed`).

- **DEBUG**:
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_profile_fallback_to_defaults` (`library_id`, `manifest_id`, `active_profile`): Records fallback to collection default variables when `environment_id` is None and no overlay profile is active.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_profile_resolved` (`profile_id`, `active_profile`, `environment_id`): Logs active profile resolution provenance.
  - `pypost/core/library_runtime_resolver.py` — `mcp_library_secret_masking_applied` (`hidden_keys_count`, `overridable_keys_count`): Emits counts of masked secrets and overridable variables without revealing sensitive variable values or names.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_manager_starting` (`instance_id`, `server_type`, `standalone`, `tool_count`): Logs manager startup details prior to starting the HTTP server daemon.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_reconcile_standalone_library_server` (`instance_id`, `library_id`, `skipping_environment_check=True`): Traces reference reconciliation for standalone library servers, recording that workspace environment checks are skipped.
  - `pypost/core/mcp_server_registry.py` — `mcp_registry_reconcile_standalone_bundled_server` (`instance_id`, `skipping_environment_check=True`): Traces reference reconciliation for standalone bundled library servers.

### Log Structure

Log format used:
- Structured logs: yes (key=value syslog-style attributes).
- Includes context: yes (`instance_id`, `library_id`, `manifest_id`, `environment_id`, `standalone`, `port`, `duration_seconds`, counts, safe non-secret variable names).
- Log levels: WARNING, INFO, DEBUG.
- Secret redaction: Secrets and sensitive credentials are never written to logs. Only variable counts (`hidden_keys_count`) and non-secret variable names are logged.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Validation Latency**: `duration_seconds` tracked via `time.monotonic()` in `LibraryRuntimeResolver.resolve` for both success and failure paths.
- **MCP Tool Call Latency**: Monitored via `track_mcp_tool_call_duration(method, status, duration_seconds)`.

### Business Metrics

Business metrics:
- **Library Validation Outcome**: Tracked via `MetricsTrackerProtocol.track_mcp_library_validation(category)`:
  - Recorded as `"success"` upon clean resolution.
  - Recorded with error category (e.g. `"profile_missing"`, `"profile_invalid"`, `"library_invalid"`, `"manifest_invalid"`, `"collection_missing"`) on failure.

### System Health Metrics

System health metrics:
- **MCP Server Instance Status Gauges**: Tracked via `MetricsTrackerProtocol.set_mcp_server_instance_counts(counts)`:
  - Aggregates real-time instance counts across states: `stopped`, `starting`, `running`, `failed`.
- **MCP Server Readiness**: `set_mcp_server_up(ready)` tracks overall MCP readiness.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`track_mcp_library_validation`, `set_mcp_server_instance_counts`, `set_mcp_server_up`)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (ELK, Loki) via structured key=value format

## Validation Results

Validation results:
- [x] Logs are correctly formatted (key=value syslog-compatible format).
- [x] Metrics are collected correctly (`_metrics.track_mcp_library_validation` and `_metrics.set_mcp_server_instance_counts`).
- [x] Logging works in error scenarios (missing required non-secret variables, validation failures, rollback events).
- [x] Large data structures are not logged (only scalar IDs, counts, and non-sensitive metadata).
- [x] Metrics are available for monitoring.
- [x] Standalone MCP execution logging verified via `tests/test_mcp_standalone_execution_repro.py::test_standalone_mcp_observability_and_logging`.
- [x] Secret masking verified: zero raw secrets leaked in logs or error messages.

## Notes

- Standalone MCP servers operate independently of workspace environments (`environment_id=None`).
- During reconciliation, standalone library servers explicitly bypass workspace environment validity checks, avoiding erroneous `failed` lifecycle states when switching or removing workspace environments.
- Secret values configured in local library overlays are masked via `hidden_keys` and never output to logs or diagnostics.
