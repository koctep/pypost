# PYPOST-1347: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:
- **EMERG**: N/A — ordinary-library lifecycle failures remain row-isolated; no process-wide
  emergency path.
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A — reconcile/reconfigure/refresh failures stay as row `failed` status or
  domain `ValueError`; no new ERROR events (avoids log-guardrail allowlist churn).
- **WARNING**:
  - `pypost/core/mcp_server_registry.py` —
    `mcp_registry_refresh_library_environment_failed instance_id=%s library_id=%s
    bundled_library=%s error=%s` — emitted when a library-sourced
    `refresh_environment` re-resolve via `LibraryRuntimeResolver` raises `ValueError`
    (missing connection, unreadable collection, or other resolve categories). Applies to
    both ordinary (`bundled_library=False`) and Built-in rows on the widened branch.
- **NOTICE**: N/A
- **INFO** (existing, reused — not newly invented):
  - `mcp_registry_stop_requested` / `mcp_registry_status … state=failed` via `stop()` and
    `_set_status()` when reconcile stops an ordinary library row for missing library,
    missing library collection, or missing environment. Status message text includes
    `missing library collection` for the new collection-resolve stop path.
- **DEBUG**:
  - `pypost/core/mcp_server_registry.py` —
    `mcp_registry_ordinary_library_collection_unresolved instance_id=%s library_id=%s` —
    emitted immediately before stop when reconcile finds the ordinary library connection
    valid but the selected collection no longer resolves.
  - `pypost/core/mcp_server_registry.py` —
    `mcp_registry_refresh_library_environment instance_id=%s library_id=%s
    bundled_library=%s variable_count=%d` — emitted after a successful library-sourced
    refresh resolve (ordinary and Built-in). Logs counts only; never variable keys/values.
  - Existing standalone skip events remain:
    `mcp_registry_reconcile_standalone_library_server` when `environment_id is None`.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (`instance_id`, `library_id`, `bundled_library`, `variable_count`,
  `error`)
- Log levels: DEBUG, INFO (reused status/stop), WARNING
- Secrets / payloads: no environment values, secrets, collection bodies, or filesystem
  paths are logged

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A — no new duration histogram for reconcile/refresh (on-demand UI
  events; resolver already logs its own validation duration events elsewhere)
- **Throughput**: N/A
- **Error rate**: unchanged — row failures still flip `mcp_server_instances{state="failed"}`
  via existing `_publish_instance_metrics`

### Business Metrics

Business metrics:
- No new Prometheus series. Ordinary-library stop/refresh outcomes remain visible through
  existing aggregate instance-state gauges and status dialogs.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A (in-memory resolve; no new background workers)
- **Component status**: `MCPServerRegistry.status` / `list_statuses` continue to expose
  per-row state and diagnostic messages including `missing library collection`

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (no new series for this Debt)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (stdlib logging / syslog-compatible levels; Loki/ELK via existing
  handlers)

## Validation Results

Validation results:
- [x] Logs are correctly formatted — key=value events on `pypost.core.mcp_server_registry`
- [x] Metrics are collected correctly — existing instance-state gauges; no regression in
  Built-in lifecycle suite
- [x] Logging works in error scenarios — collection-file removal triggers unresolved DEBUG
  + stop/status INFO; resolve failure path has WARNING (silent `continue` removed)
- [x] Large data structures are not logged — only IDs, booleans, counts, and exception
  string; refresh success test asserts default URL and updated workspace values are absent
- [x] Metrics are available for monitoring — via existing `MetricsTrackerProtocol`
- [x] Automated coverage —
  `tests/test_mcp_library_lifecycle.py::test_ordinary_library_lifecycle_observability_and_logging`

## Notes

- Widened `refresh_environment` logging covers Built-in and ordinary library rows with the
  same event names and a `bundled_library` discriminator so operators can filter without a
  second merge of event catalogs.
- Reconfigure rejection for unresolved ordinary collections raises
  `ValueError("… missing library collection")` and relies on existing controller /
  presenter error handling; no additional ERROR log was added (guardrail-safe).
- Ready for orchestrator Step 6 review (`[/]` left for gate owner).
