# PYPOST-1352: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging for Built-in MCP server lifecycle reconciliation, reconfigure transitions,
environment updates, and controller save operations is integrated across syslog levels in
`pypost/core/mcp_server_registry.py` and `pypost/ui/mcp_server_controller.py`:

- **EMERG**: None (runtime lifecycle failures and invalid save attempts are isolated to individual
  server rows and do not cause unrecoverable system failures).
- **ALERT**: None.
- **CRIT**: None.
- **ERR**: None (unresolvable built-in servers, uncurated collection paths, and missing environments
  set status to `failed` or return safe domain errors gracefully without unhandled exceptions).
- **WARNING**:
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_reconfigure_rolled_back instance_id=%s port=%d reason=%s` — logged when
    candidate reconfiguration fails or times out and the registry rolls back to previous manager
    (`instance_id`, `port`, `reason`).
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_library_save_failed outcome=%s` — logged when an atomic save transaction fails to commit
    settings (`outcome`).
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_library_save_rollback_failed` — logged with exception info if restoring previous settings
    or registry snapshot encounters an error.
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_library_save_rolled_back` — logged when settings transaction rolls back cleanly after a
    subsequent installation failure.
- **NOTICE**: None.
- **INFO**:
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_start_requested instance_id=%s port=%d` — logged when a server instance startup
    is requested (`instance_id`, `port`).
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_stop_requested instance_id=%s port=%d` — logged when a server instance stop is
    requested (`instance_id`, `port`).
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_status instance_id=%s state=%s message_present=%s` — logged whenever a server
    instance transitions state (`instance_id`, `state`, `message_present`).
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_library_save_committed` — logged when an atomic settings transaction successfully commits
    (`store.commit`).
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_servers_persist_requested reason=%s count=%d` — logged when non-store controller saves
    persist configuration (`reason`, `count`).
  - `pypost/core/library_runtime_resolver.py`:
    `mcp_library_runtime_validation_started library_id=%s manifest_id=%s` — logged when runtime
    resolver resolves preflight inputs (`library_id`, `manifest_id`).
  - `pypost/core/library_runtime_resolver.py`:
    `mcp_library_runtime_validation_completed duration_seconds=%.3f request_count=%d` — logged
    when runtime resolution completes (`duration_seconds`, `request_count`, `variable_count`).
- **DEBUG**:
  - `pypost/ui/mcp_server_controller.py`:
    `mcp_server_activity_unavailable instance_id=%s` — logged when activity log is queried for an
    endpoint that has never started.
  - `pypost/core/builtin_collections.py`:
    `builtin_collection_entry_loaded entry_id=%s path=%s env=%s` — logged for each validated
    curated entry loaded into the view (`entry_id`, `path`, `env`).

### Log Structure

Log format used:
- Structured logs: yes (consistent key=value attributes formatted into event messages).
- Includes context: yes (`instance_id`, `port`, `state`, `message_present`, `reason`, `outcome`).
- Log levels: DEBUG, INFO, WARNING.
- Secret values or full payloads logged: no (credentials and request bodies are excluded; only
  identifiers, ports, and outcome indicators are logged).

## Diagnostic State and Failure Indicators

In addition to syslog structured logging, `MCPServerRegistry` and `McpServerSettingsController`
expose clear diagnostics through status reporting, signals, and domain exceptions:

- **Missing Built-in Collection Diagnostic**:
  - Trigger: During `reconcile_references`, if `configuration.bundled_library=True` and its
    `library_collection_path` is not found in `BuiltinCollectionView.list_entries()`, the server is
    stopped and marked failed.
  - Formatted message:
    `{instance_id} cannot run: missing built-in collection for port {port}`
  - Logged event:
    `mcp_registry_status instance_id={instance_id} state=failed message_present=True`
- **Missing Environment Diagnostic**:
  - Trigger: During `reconcile_references`, if `configuration.bundled_library=True` and its
    `environment_id` is not in `valid_environment_ids` (or deleted from environment storage), the
    server is stopped and marked failed.
  - Formatted message:
    `{instance_id} cannot run: missing environment for port {port}`
  - Logged event:
    `mcp_registry_status instance_id={instance_id} state=failed message_present=True`
- **Reconfigure Validation Failure**:
  - Trigger: During `reconfigure(instance_id, configuration)`, if an uncurated collection path or
    missing environment is supplied, `_validate_replacement_references` raises an explicit
    `ValueError`:
    `MCP server {instance_id} references a missing built-in collection` or
    `MCP server {instance_id} references a missing environment`.
  - The live running manager continues serving clients unaffected.
- **Controller Save Validation Failure**:
  - Trigger: When saving a Built-in row in `McpServerSettingsController.upsert_mcp_server`, if
    `library_collection_path` is not among curated catalog entries, save rejects immediately with:
    `ValueError: builtin_invalid: uncurated built-in collection path '{path}'`.
  - If `library_selection` is incomplete:
    `ValueError: builtin_invalid: built-in identity is incomplete`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Sub-millisecond in-memory resolution for Built-in server preflight via
  `_BundledLibraryAdapter` and `BuiltinCollectionView`.
- **Throughput**: N/A (lifecycle and save operations are on-demand events).
- **Error rate**: Tracked via `failed` instance count in `_publish_instance_metrics()`.

### Business Metrics

Business metrics:
- Active MCP server counts per lifecycle state (`stopped`, `starting`, `running`, `failed`)
  published via `MetricsTrackerProtocol.set_mcp_server_instance_counts(counts)`.
- MCP library save operations tracked via `MetricsTrackerProtocol.track_mcp_library_save(category,
  duration)`.

### System Health Metrics

System health metrics:
- **Resource usage**: Minimal memory footprint; no overlay files created or persisted on disk for
  Built-in rows (`overlay={}`).
- **Component status**: Monitored through `MCPServerRegistry.status(instance_id)` and
  `list_statuses()`.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (syslog, Loki, ELK, standard Python logging handlers)

## Validation Results

Validation results:
- [x] Logs are correctly formatted: Structured key=value attributes across DEBUG, INFO, WARNING.
- [x] Metrics are collected correctly: `MCPServerRegistry._publish_instance_metrics` updates state
  counts on status transitions; `track_mcp_library_save` records commit/rollback durations.
- [x] Logging works in error scenarios: Verified via test cases covering uncurated collection paths,
  missing environments, and failed startups.
- [x] Large data structures are not logged: Only identifiers, ports, paths, and entry counts.
- [x] Metrics are available for monitoring: Exposed through `MetricsTrackerProtocol`.
- [x] Automated test verification: Verified via
  `tests/test_mcp_builtin_lifecycle.py::test_builtin_lifecycle_observability_and_logging`
  and `tests/test_mcp_builtin_startup.py::test_builtin_server_observability_and_logging`
  asserting structured logs (`mcp_registry_start_requested`, `mcp_registry_status`,
  `mcp_library_save_committed`, `mcp_registry_stop_requested`), status transitions, and diagnostic
  messages using `caplog`.

## Notes

All operations in `MCPServerRegistry` and `McpServerSettingsController` maintain complete process
and lifecycle isolation: a failure in one built-in server row immediately transitions to `"failed"`
with descriptive diagnostics and never blocks or interferes with other configured servers.
