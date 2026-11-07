# PYPOST-1466: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: N/A — worker process crashes, backoff scheduling, and restart attempts are contained
  within the isolated supervisor lifecycle and never threaten host application stability.
- **ALERT**: N/A — isolated worker crashes or retry exhaustion on one server do not affect
  neighboring MCP servers or peer processes.
- **CRIT**: N/A — unrecoverable worker exits transition only the affected server to terminal
  `failed` status.
- **ERR**:
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`, `_handle_restart_failure`):
    `mcp_worker_restart_exhausted instance_id=%s attempts=%d max_retries=%d exitcode=%s` — logged
    when a crashed worker reaches or exceeds `max_retries`, emitting attempts count, retry
    limit, and
    last process exit code without leaking tool definitions, variable values, or secret payloads.
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`):
    `mcp_worker_unexpected_exit instance_id=%s pid=%s exitcode=%s prior_state=%s` — logged when
    a worker exits unexpectedly while auto-restart is disabled (`enabled=False`) or during initial
    startup (`prior_state=starting`, `FR7`).
  - `pypost/core/mcp_server_registry.py` (`_handle_worker_unexpected_exit`):
    `mcp_registry_unexpected_child_exit instance_id=%s port=%d exitcode=%s prior_state=%s`
    — logged when child worker exit is unhandled by retry policy and triggers terminal server
    failure.
- **WARNING**:
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`):
    `mcp_worker_terminate instance_id=%s pid=%s signal=SIGTERM` and
    `mcp_worker_kill instance_id=%s pid=%s signal=SIGKILL`
    — logged when a stopping worker fails to exit within graceful stop budget and requires
    signal escalation.
- **NOTICE**: N/A — operational supervisor lifecycle events use standard `INFO` level.
- **INFO**:
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`, `_handle_restart_failure`):
    `mcp_worker_restart_scheduled instance_id=%s attempt=%d max_retries=%d delay_s=%.2f exitcode=%s`
    — records scheduled auto-restart attempt with monotonic backoff delay and previous exit code.
  - `pypost/core/mcp_process_supervisor.py` (`_attempt_restart`):
    `mcp_worker_restarted instance_id=%s pid=%s attempt=%d max_retries=%d` — records successful
    worker recovery with new process PID and attempt counter.
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`):
    `mcp_worker_restart_counter_reset instance_id=%s pid=%s uptime_s=%.2f previous_retry_count=%d`
    — records reset of consecutive retry counter after healthy uptime window
    (`uptime_s >= healthy_reset_window_s`, `FR4`).
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`, `shutdown`):
    `mcp_worker_restart_cancelled instance_id=%s attempt=%d reason=%s` — records immediate
    cancellation of pending backoff retries when stopped by operator (`reason=operator_stop`) or
    daemon shutdown (`reason=supervisor_shutdown`, `FR6`).
  - `pypost/core/mcp_server_registry.py` (`_handle_worker_restarting`):
    `mcp_registry_worker_restarting instance_id=%s port=%d attempt=%d`
    `max_retries=%d delay_s=%.2f exitcode=%s`
    — records registry-level notification of transitional recovery and backoff scheduling.
  - `pypost/core/mcp_server_registry.py` (`_handle_worker_restarted`):
    `mcp_registry_worker_restarted instance_id=%s attempt=%d`
    — records registry-level notification of successful worker respawn and transition
    back to `running`.
  - `pypost/core/mcp_server_registry.py` (`_set_status`):
    `mcp_registry_status instance_id=%s state=%s message_present=%s` — records server lifecycle
    status transitions (`starting`, `running`, `failed`, `stopped`) with sanitized presence flag.
- **DEBUG**:
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_ipc_ack instance_id=%s pid=%s correlating=%s` — traces worker IPC message
    acknowledgments during startup and tool/variable updates without serializing payload data.

### Log Structure

Log format used:

- Structured logs: yes (`event_name key=value ...`)
- Includes context: yes (`instance_id`, `pid`, `port`, `attempt`, `attempts`, `max_retries`,
  `delay_s`, `exitcode`, `uptime_s`, `previous_retry_count`, `reason`, `state`, `message_present`)
- Log levels: DEBUG, INFO, WARNING, ERROR (ERR)

### Secret Safety Verification (`FR8`)

All supervisor and registry log events strictly omit sensitive data:

1. **Secret Variables & Values**: Neither variable maps nor resolved secrets
   (`super-secret-token-v1`, `super-secret-token-v2-rotated`) are ever logged. `_WorkerSpawnSpec`
   stores secret keys in memory for process IPC but never serializes them to log messages.
2. **Variable Keys & Environment Maps**: Keys such as `col_stage` or `env_region` are never
   dumped to log strings.
3. **Upstream URLs & Headers**: In proxy and standard MCP modes, upstream URLs
   (e.g., `http://127.0.0.1:<stub_port>`) and HTTP header names/values (`X-Secret-Token`) are
   excluded from supervisor logs.
4. **Tool Definitions & Request Payloads**: Tool schemas, request bodies, and JSON-RPC payloads
   are omitted; only aggregate counts (`tool_count=%d`) are logged on worker spawn.
5. **Sanitized Status Logging**: Registry status messages use `message_present=bool(message)` in
   `mcp_registry_status` to prevent unstructured error messages from leaking sensitive strings
   into standard log streams.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: `MCPServerImpl._call_tool_inner` records tool call latency via
  `record_mcp_call_outcome` in `pypost/core/mcp_server_impl.py`.
- **Throughput**: `MCPServerImpl._call_tool_inner` tracks incoming requests and tool invocations via
  `track_mcp_request_received` and `record_mcp_call_outcome`.
- **Error rate**: tracked via `outcome="error"` in `record_mcp_call_outcome` and `failed` instance
  state counts in `MCPServerRegistry._publish_instance_metrics`.

### Business Metrics

Business metrics:

- `mcp_server_instances{state}`: gauge updated by `MCPServerRegistry._publish_instance_metrics` via
  `set_mcp_server_instance_counts`. During backoff recovery, the server transitions to
  `state="starting"`, communicating active recovery to operators and monitoring dashboards. When
  retries exhaust, the server transitions to `state="failed"`.

### System Health Metrics

System health metrics:

- **Resource usage**: Exponential backoff delays
  ($\min(\text{max\_backoff}, \text{initial\_backoff} \times \text{multiplier}^{k-1})$)
  prevent tight crash-loops from consuming host CPU, file descriptors, or process table slots.
- **Component status**: `MCPServerStatus(id, state, message)` exposes current lifecycle status
  (`stopped`, `starting`, `running`, `failed`) and descriptive diagnostic text:
  - During backoff:
    `"Restarting after unexpected exit (attempt {attempt}/{max_retries}, delay {delay_s:.1f}s)"`
  - On exhaustion:
    `"{instance_id} on port {port}: unexpected worker exit (exitcode={exitcode})"`

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`mcp_server_instances` gauge publishing instance counts across
  `stopped`, `starting`, `running`, `failed`)
- [ ] Grafana dashboards (existing server instance status panels track recovering `starting` and
  `failed` counts)
- [ ] Alerting rules (alerting on sustained `failed` instances or `mcp_worker_restart_exhausted`
  log rate)
- [x] Log aggregation (structured key-value event streams for ELK, Loki, or Datadog)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`mcp_worker_restart_scheduled`, `mcp_worker_restarted`,
  `mcp_worker_restart_exhausted`, `mcp_worker_restart_counter_reset`, and
  `mcp_worker_restart_cancelled` verified with exact key-value assertions)
- [x] Metrics are collected correctly (`_publish_instance_metrics` updates state counts on every
  recovery transition)
- [x] Logging works in error scenarios (crash recovery, retry exhaustion, and startup failure paths
  emit expected structured logs)
- [x] Large data structures are not logged (`tools`, `variables`, `headers`, `upstream_url`, and
  payloads are completely absent from logs)
- [x] Metrics are available for monitoring (`mcp_server_instances` reflects live status)

## Notes

### Automated Log Assertions in `tests/test_mcp_process_autorestart_repro.py`

Automated test assertions using pytest's `caplog` fixture verify that:

1. **`test_auto_restart_recovers_crashed_worker_with_exponential_backoff_and_latest_state`**:
   - Asserts `mcp_worker_restart_scheduled` is emitted with `instance_id`, `attempt=1`,
     `max_retries=3`, `delay_s=0.10`, and `exitcode`.
   - Asserts `mcp_worker_restarted` is emitted with `instance_id`, `pid=<new_pid>`, `attempt=1`, and
     `max_retries=3`.
   - Asserts secret tokens (`super-secret-token-v1`, `super-secret-token-v2-rotated`), URLs
     (`http://127.0.0.1:<stub_port>`), headers (`X-Secret-Token`), and variable keys (`col_stage`,
     `env_region`) are **never** present in captured log text (`FR8`).
2. **`test_auto_restart_exhaustion_transitions_to_failed_after_max_retries`**:
   - Asserts `mcp_worker_restart_scheduled` is emitted twice with progressive exponential delays
     (`delay_s=0.08`, `delay_s=0.16`).
   - Asserts `mcp_worker_restart_exhausted` is emitted with `instance_id`, `attempts=2`,
     `max_retries=2`, and `exitcode`.
3. **`test_healthy_reset_window_resets_retry_counter_for_later_crash`**:
   - Asserts `mcp_worker_restart_counter_reset` is emitted with `instance_id`, `pid`,
     `uptime_s`, and `previous_retry_count=1`.
4. **`test_operator_stop_and_shutdown_cancel_pending_backoff_immediately`**:
   - Asserts `mcp_worker_restart_cancelled` is emitted with `instance_id=srv-stop`, `attempt=1`,
     and `reason=operator_stop`.
   - Asserts `mcp_worker_restart_cancelled` is emitted with `instance_id=srv-shutdown`, `attempt=1`,
     and `reason=supervisor_shutdown`.
5. **`test_default_policy_disabled_fails_immediately_without_retry`**:
   - Asserts `mcp_registry_unexpected_child_exit` is logged on crash without any
     `mcp_worker_restart_scheduled` events.
