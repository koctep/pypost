# PYPOST-1351: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging for Built-in MCP server startup, lifecycle, reference resolution, and
failures is implemented in `pypost/core/mcp_server_registry.py`, integrated with domain
events from `pypost/core/builtin_collections.py` and `pypost/core/predefined_library.py`:

- **EMERG**: None (runtime lifecycle failures are isolated to individual server rows and do not
  cause unrecoverable system failures).
- **ALERT**: None.
- **CRIT**: None.
- **ERR**: None (unresolvable built-in servers, port conflicts, and candidate bind failures
  set status to `failed` and emit structured logs/signals gracefully without unhandled exceptions).
- **WARNING**:
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_reconfigure_rolled_back instance_id=%s port=%d reason=%s` — logged when
    candidate reconfiguration fails or times out and the registry rolls back to the previous
    manager (`instance_id`, `port`, `reason`).
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_unavailable reason=%s` — logged when bundled examples root is missing
    or invalid (`reason`, `root`).
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_discovery_failed` — logged when underlying predefined library discovery
    fails.
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_catalog_missing path=%s` — logged when `builtin-collections.yaml` is
    missing (`path`).
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_catalog_parse_failed reason=%s` — logged when catalog YAML is
    malformed (`reason`).
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_catalog_invalid_root` / `builtin_collections_catalog_invalid_entries` —
    logged when catalog schema is invalid.
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_entry_undeclared path=%s` — logged when a catalog entry is not in the
    library manifest (`path`).
  - `pypost/core/predefined_library.py`:
    `predefined_library_discovery_failed library_id=%s error_type=%s` — logged when bundled
    library discovery fails (`library_id`, `error_type`).
  - `pypost/core/predefined_library.py`:
    `predefined_library_collections_missing library_id=%s count=%d` — logged when declared
    collections are missing (`library_id`, `count`).
  - `pypost/core/predefined_library.py`:
    `predefined_library_collection_invalid library_id=%s path=%s` — logged when a collection
    file cannot be parsed (`library_id`, `path`).
- **NOTICE**: None.
- **INFO**:
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_start_requested instance_id=%s port=%d` — logged when a server instance
    startup is requested (`instance_id`, `port`).
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_stop_requested instance_id=%s port=%d` — logged when a server instance
    stop is requested (`instance_id`, `port`).
  - `pypost/core/mcp_server_registry.py`:
    `mcp_registry_status instance_id=%s state=%s message_present=%s` — logged whenever a
    server instance transitions state (`instance_id`, `state`, `message_present`).
  - `pypost/core/builtin_collections.py`:
    `builtin_collections_list_completed library_id=%s entry_count=%d` — logged when curated
    entries are listed (`library_id`, `entry_count`).
  - `pypost/core/predefined_library.py`:
    `predefined_library_discovery_started library_id=%s` — logged when discovering bundled
    library (`library_id`).
  - `pypost/core/predefined_library.py`:
    `predefined_library_discovery_completed library_id=%s collection_count=%d` — logged when
    bundled library discovery succeeds (`library_id`, `collection_count`).
  - `pypost/core/library_runtime_resolver.py`:
    `mcp_library_runtime_validation_started library_id=%s manifest_id=%s` — logged when runtime
    inputs resolution begins (`library_id`, `manifest_id`).
  - `pypost/core/library_runtime_resolver.py`:
    `mcp_library_runtime_validation_completed duration_seconds=%.3f request_count=%d` — logged
    when runtime resolution completes (`duration_seconds`, `request_count`, `variable_count`).
- **DEBUG**:
  - `pypost/core/builtin_collections.py`:
    `builtin_collection_entry_loaded entry_id=%s path=%s env=%s` — logged for each validated
    curated entry loaded into the view (`entry_id`, `path`, `env`).
  - `pypost/core/variable_resolver.py`:
    `variable_resolution_completed total_resolved=%d` — logged during environment variable
    resolution for the server runtime.

### Log Structure

Log format used:
- Structured logs: yes (consistent key=value attributes formatted into event messages).
- Includes context: yes (`instance_id`, `port`, `state`, `library_id`, `collection_path`, `reason`).
- Log levels: DEBUG, INFO, WARNING.
- Secret values or full payloads logged: no (credentials and request bodies are masked or omitted;
  only instance IDs, ports, entry IDs, and file paths are logged).

## Diagnostic State and Error Exposure

In addition to syslog structured logging, `MCPServerRegistry` exposes diagnostics through
`McpServerStatus.message` and the `status_changed` signal (`instance_id`, `state`, `message`):

- **Missing Built-in Collection Diagnostic**:
  When a Built-in server (`bundled_library=True`) fails runtime resolution — either because its
  `library_collection_path` is not a curated entry in `BuiltinCollectionView` or because the
  collection file is unresolvable — the registry transitions the server state to `"failed"` and
  formats the diagnostic message:
  ```
  <instance_id> cannot start: missing built-in collection for port <port>
  ```
  This is exposed via `registry.status(instance_id).message` and logged as:
  ```
  mcp_registry_status instance_id=<instance_id> state=failed message_present=True
  ```
- **View Diagnostics**:
  Underlying collection issues populate `BuiltinCollectionView.diagnostics`, surfacing
  human-readable explanations for catalog or schema anomalies without crashing the application.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Sub-millisecond in-memory resolution via `_BundledLibraryAdapter` and
  `BuiltinCollectionView`.
- **Throughput**: N/A (startup lifecycle operations occur on server enable/start).
- **Error rate**: Tracked via `failed` instance count in `_publish_instance_metrics()`.

### Business Metrics

Business metrics:
- Active MCP server counts per lifecycle state (`stopped`, `starting`, `running`, `failed`)
  published via `MetricsTrackerProtocol.set_mcp_server_instance_counts(counts)`.

### System Health Metrics

System health metrics:
- **Resource usage**: Minimal memory overhead; `_BundledLibraryAdapter` references the shared
  `BuiltinCollectionView` and reads collection requests freshly on demand without retaining
  duplicate heavy caches.
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
  gauges on every status change.
- [x] Logging works in error scenarios: Verified via test cases covering invalid collection paths,
  missing references, and failed startups.
- [x] Large data structures are not logged: Only identifiers, ports, paths, and entry counts.
- [x] Metrics are available for monitoring: Exposed through `MetricsTrackerProtocol`.
- [x] Automated test verification: Verified via
  `tests/test_mcp_builtin_startup.py::test_builtin_server_observability_and_logging`
  asserting structured logs (`mcp_registry_start_requested`, `mcp_registry_status`,
  `predefined_library_discovery_*`, `builtin_collections_*`) and diagnostic messages using `caplog`.

## Notes

All operations in `MCPServerRegistry` and `_BundledLibraryAdapter` maintain complete process and
lifecycle isolation: a failure in one built-in server row immediately transitions to `"failed"`
with descriptive diagnostics and never blocks or interferes with other configured servers.
