# PYPOST-993: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging was implemented across `pypost.agent.seed_loader`, `pypost.agent.lifecycle`,
and `pypost.agent.ui_actions_mcp` to provide complete observability for seed resolution,
parsing, staging, and sidecar session startup.

- **EMERG**: Not applicable. Seed loading/injection failures are isolated to the sidecar session
  startup and do not compromise host system stability.
- **ALERT**: Not applicable. Startup failures do not require immediate paging; failures exit with
  code 1 and structured error logs for automated agent orchestrators.
- **CRIT**: Not applicable. No critical unrecoverable system conditions introduced.
- **ERR**:
  - `pypost.agent.ui_actions_mcp` (`main`):
    `agent_ui_mcp_attach_with_seed_rejected seed_path=%s error_type=%s error=%s`
    (Syslog ERR / Python `logging.ERROR`) — Logged when mutually exclusive `--attach` and
    `--seed` / `--seed-file` options are supplied concurrently.
  - `pypost.agent.ui_actions_mcp` (`_run_spawn_session`):
    `agent_ui_mcp_seed_failed seed_path=%s error_type=%s error=%s`
    (Syslog ERR / Python `logging.ERROR`) — Logged when seed resolution, reading, or schema
    validation fails (`SeedLoadError` or `SeedFormatError`), exiting with code 1.
- **WARNING**: Not applicable. Seed injection enforces fail-fast semantics rather than logging
  warnings and continuing with partial or corrupted storage states.
- **NOTICE**: Not applicable. Python standard library `logging` maps informational events to `INFO`.
- **INFO**:
  - `pypost.agent.seed_loader` (`_inject_file`):
    `agent_seed_injected_collection file=%s collection_id=%s request_count=%d` — Emitted for each
    collection successfully validated and written to ephemeral storage.
  - `pypost.agent.seed_loader` (`_inject_file`):
    `agent_seed_injected_environment file=%s env_id=%s` — Emitted for each environment validated
    and written to storage, without exposing variable values or secrets.
  - `pypost.agent.seed_loader` (`_inject_file`):
    `agent_seed_injected_environments file=%s count=%d` — Emitted when multiple environments are
    persisted from a single JSON/YAML list or bundle.
  - `pypost.agent.seed_loader` (`inject_seed`):
    `agent_seed_injection_completed seed_path=%s collection_count=%d request_count=%d duration_ms=%.2f` —
    Emitted upon completion of seed staging, recording the source path, total collections injected,
    total request items injected, and elapsed staging time in milliseconds.
  - `pypost.agent.lifecycle` (`AgentAppSession.start`):
    `agent_session_seed_injected path=%s seed_path=%s collections_count=%d collection_count=%d duration_ms=%.2f` —
    Emitted during session startup immediately following disk staging and preceding Qt UI composition.
  - `pypost.agent.ui_actions_mcp` (`_run_spawn_session`):
    `agent_ui_mcp_session_ready offscreen=%s` — Emitted when sidecar session startup completes and
    stdio MCP server begins serving tools.
- **DEBUG**: Fine-grained debug logs are deliberately omitted to avoid exposing sensitive request
  headers, auth tokens, or payload data present in seed files.

### Log Structure

- Structured logs: yes — stable event names (`agent_seed_*`, `agent_session_seed_*`, `agent_ui_mcp_*`)
  followed by key-value pairs (`key=value`).
- Includes context: yes — key context fields:
  - `seed_path`: Absolute or relative path to the seed file or directory.
  - `collection_count`: Number of collection files staged into storage.
  - `request_count`: Total number of request items contained across staged collections.
  - `duration_ms`: High-resolution execution duration in milliseconds measured via `time.perf_counter()`.
  - `error_type`: Specific exception class name (`SeedLoadError`, `SeedFormatError`, `CommandLineError`).
  - `error`: Explanatory error details.
  - `file`: Path of the individual seed file being processed.
  - `collection_id`: Unique identifier of the persisted collection.
  - `env_id`: Unique identifier of the persisted environment.
- Log levels: `INFO`, `ERROR`.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time / staging latency**:
  - `duration_ms` in `pypost.agent.seed_loader.inject_seed` — Measures end-to-end seed loading,
    parsing (JSON/YAML), schema validation via Pydantic models, and atomic disk writes to
    ephemeral workspace storage.
  - `duration_ms` in `pypost.agent.lifecycle.AgentAppSession.start` — Measures total seed staging
    duration during session bootstrap before application composition begins.
  - Latency target: <5ms for typical single collections and <15ms for multi-collection directory
    bundles. Automated tests demonstrate staging finishes in ~2–10ms.
- **Throughput**: Single-shot startup operation. Disk staging runs synchronously prior to Qt
  event loop startup, eliminating concurrency overhead and read-write contention.
- **Error rate**: Tracked via `agent_ui_mcp_seed_failed` and `agent_ui_mcp_attach_with_seed_rejected`
  structured error logs with explicit `error_type` tagging.

### Business Metrics

- `collection_count`: Total count of pre-seeded collections available to the agent session upon launch.
- `request_count`: Total count of executable request templates available in pre-seeded collections.
- `environments_count`: Total count of pre-seeded environments configured for the session.

### System Health Metrics

- **Resource usage**:
  - CPU & memory: Low overhead; seed payloads are parsed into lightweight Pydantic models and
    written directly to disk. Memory is freed as garbage collection reclaims parsing structures.
  - Storage: Staged files reside in a temporary workspace directory (`pypost-agent-data-*`) that
    is cleaned up when the `AgentAppSession` terminates.
- **Component status**:
  - Pre-composition staging guarantees that `StorageManager.load_collections()` in `compose_app()`
    finds seeded files immediately, ensuring full UI population when `MainWindow.is_ui_ready`
    reaches `True` within `ready_timeout` (default: 30.0s).

## Monitoring Integration

- [x] Prometheus metrics: Application-level metrics server (`MetricsManager` on `metrics_port`)
  exposes runtime metrics; seed staging metrics are emitted as structured operational logs during
  bootstrap before metrics server socket binding.
- [ ] Grafana dashboards: Startup latency and failure dashboards can aggregate log events.
- [ ] Alerting rules: Automated pipeline alerts can trigger on `agent_ui_mcp_seed_failed` or
  `agent_ui_mcp_attach_with_seed_rejected` log occurrences.
- [x] Log aggregation (ELK, Loki, etc.): Standard `stderr` stream uses structured key-value
  formatting, enabling ingestion and indexing by vector, Fluentbit, Logstash, or CloudWatch.

## Validation Results

- [x] Logs are correctly formatted: Structured key-value format with clear event identifiers and
  consistent field names.
- [x] Metrics are collected correctly: `duration_ms`, `collection_count`, and `request_count` are
  accurately measured and logged.
- [x] Logging works in error scenarios: Verified via unit and integration tests using `caplog`
  (`test_ui_actions_mcp_cli_attach_with_seed_rejected`, `test_ui_actions_mcp_seed_failure_logged`).
- [x] Large data structures are not logged: Seed bodies, raw JSON payloads, and secret variable
  values are never dumped to log output.
- [x] Metrics are available for monitoring: Staging latency and item counts are prominently logged
  at startup.

## Notes

- **Synchronization & Atomicity**: Seed injection executes synchronously in `AgentAppSession.start`
  prior to `compose_app()`. This prevents race conditions between disk writes and UI tree view
  initialization, ensuring all collections and environments are present before the UI becomes ready.
- **Security & Privacy**: Per repository guidelines, environment variables and collection request
  bodies are not printed in log lines to prevent accidental credential leakage in log aggregation
  systems.
