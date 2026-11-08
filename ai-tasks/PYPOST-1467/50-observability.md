# PYPOST-1467: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging implemented for IPC protocol version negotiation and rejection:

- **EMERG**: N/A — protocol version mismatches are isolated to individual worker processes
  or IPC envelopes and do not threaten the host application stability.
- **ALERT**: N/A — mismatch rejection contained to single MCP worker instance.
- **CRIT**: N/A — version incompatibility triggers controlled rejection rather than
  unhandled crash.
- **ERR**:
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_supervisor_ipc_version_rejected instance_id=%s received_v=%s supported=%s error=%s`
    Logged when the supervisor receives an IPC message envelope with an unsupported or missing
    protocol version. If the worker is in `starting` state, supervisor marks the worker state as
    `failed`, sets `last_error`, and unblocks waiting callers via `started_event.set()`. If the
    worker is in `running` state, the message is discarded without corrupting supervisor state.
- **WARNING**:
  - `pypost/core/mcp_worker_process.py` (`worker_main`):
    `mcp_worker_ipc_version_rejected received_v=%s supported=%s error=%s`
    Logged when the worker process receives an IPC message envelope from the supervisor with an
    unsupported or missing protocol version. If the worker is in initial startup (`store is None`),
    it replies with `START_FAILED` and exits cleanly. If the worker is already running (`store`
    is initialized), it replies with `WORKER_ERROR` and continues serving.
- **NOTICE**: N/A — standard operational lifecycle transitions use `INFO` level.
- **INFO**:
  - Standard worker lifecycle events (`mcp_worker_started`, `mcp_worker_spawned`) continue to
    record successful startup and process tracking.
- **DEBUG**: N/A — version negotiation is captured at WARNING/ERROR levels for auditability.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value ...`)
- Includes context: yes (`instance_id`, `received_v`, `supported`, `error`)
- Log levels: WARNING, ERROR (ERR)

### Secret Safety Verification

All version negotiation log events strictly avoid logging sensitive data:
1. **No Sensitive Payloads**: Version validation occurs before message body processing; payload
   contents, tool arguments, environment variables, and auth tokens are never logged.
2. **Metadata Only**: Only the protocol version integer (`received_v`), set of supported
   versions (`supported`), error message (`error`), and `instance_id` are emitted.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Negligible overhead ($O(1)$ set lookup against `SUPPORTED_MSG_VERSIONS`
  frozenset upon ingress of each IPC envelope).
- **Throughput**: No degradation to IPC message throughput.
- **Error rate**: Incompatible envelopes are rejected immediately without entering message queues.

### Business Metrics

Business metrics:
- `mcp_server_instances{state="failed"}`: Updated by supervisor / registry when a worker fails
  to start due to an incompatible IPC version.

### System Health Metrics

System health metrics:
- **Resource usage**: Fast rejection on startup prevents hung processes or leaked file descriptors
  and child processes.
- **Component status**: Worker transitions to `failed` with descriptive `last_error` containing
  incompatible version details.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`mcp_server_instances{state="failed"}`)
- [ ] Grafana dashboards (tracks failed instance counts and alerts on worker start failures)
- [ ] Alerting rules (alert on log event `mcp_supervisor_ipc_version_rejected` indicating binary
  skew between supervisor and worker environments)
- [x] Log aggregation (structured key-value event streams for ELK, Loki, or Datadog)

## Validation Results

Validation results:
- [x] Logs are correctly formatted:
  - `mcp_supervisor_ipc_version_rejected` formatted with `instance_id`, `received_v`, `supported`,
    and `error`.
  - `mcp_worker_ipc_version_rejected` formatted with `received_v`, `supported`, and `error`.
- [x] Metrics are collected correctly (`mcp_server_instances` updated on startup failure).
- [x] Logging works in error scenarios (both startup mismatch and runtime mismatch tested).
- [x] Large data structures are not logged (only metadata fields emitted).
- [x] Metrics are available for monitoring.

## Notes

### Automated caplog Verification in `tests/test_mcp_ipc_protocol_version_repro.py`

Automated test assertions using pytest's `caplog` fixture verify that:

1. **`test_supervisor_ingress_start_rejection_on_mismatched_version`**:
   - Asserts `mcp_supervisor_ipc_version_rejected` is logged at `ERROR` level.
   - Asserts context `received_v=99` is included in the log message.
   - Verifies worker state transitions to `failed` and `started_event` is set.

2. **`test_supervisor_ingress_running_rejection_on_mismatched_version`**:
   - Asserts `mcp_supervisor_ipc_version_rejected` is logged at `ERROR` level.
   - Asserts context `received_v=99` is included in the log message.
   - Verifies worker state remains `running` and invalid message is discarded.

3. **`test_worker_ingress_start_rejection_logs_version_mismatch`**:
   - Asserts `mcp_worker_ipc_version_rejected` is logged at `WARNING` level.
   - Asserts `received_v=99` and `supported=` are included in the log message.
   - Verifies `START_FAILED` is sent and worker exits cleanly.

4. **`test_worker_ingress_runtime_rejection_logs_version_mismatch`**:
   - Asserts `mcp_worker_ipc_version_rejected` is logged at `WARNING` level.
   - Asserts `received_v=99` is included in the log message.
   - Verifies `WORKER_ERROR` is sent and worker remains alive.

### Operational Guidance

- A sudden occurrence of `mcp_supervisor_ipc_version_rejected` or
  `mcp_worker_ipc_version_rejected` in production logs typically indicates version drift between
  the running host application and spawned child worker environments (e.g. partial deployment or
  stale virtual environment).
- Remediation: Ensure supervisor and worker environments share identical package versions and
  restart affected MCP servers.
