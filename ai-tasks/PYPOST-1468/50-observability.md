# PYPOST-1468: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging implemented for isolated MCP worker active HEARTBEAT watchdog:

- **EMERG**: N/A — worker freeze or heartbeat timeout is contained to the individual worker process
  and does not threaten host application integrity or stability.
- **ALERT**: N/A — runaway or hung worker termination is handled automatically by the supervisor.
- **CRIT**: N/A — watchdog escalation terminates unresponsive workers rather than allowing
  uncontrolled host degradation.
- **ERR**:
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`):
    `mcp_worker_heartbeat_timeout instance_id=%s pid=%s timeout_s=%.2f`
    Logged at ERROR severity when a pending heartbeat probe sent to a child worker has remained
    unanswered for longer than `heartbeat_policy.timeout_s`. The supervisor forcefully terminates
    the hung child process via `SIGTERM` followed by `SIGKILL` escalation, sets
    `record.last_error = f"heartbeat timeout ({timeout_s}s)"`, and transitions the worker to
    restarting or failed state.
- **WARNING**:
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_heartbeat_pong_mismatch instance_id=%s expected=%s got=%s`
    Logged at WARNING severity when the supervisor receives a `HEARTBEAT_PONG` message whose nonce
    does not match the current `record.pending_heartbeat_nonce` (e.g. unsolicited pong, stale/late
    reply received after a timeout, or nonce corruption).
- **NOTICE**: N/A — lifecycle transitions follow standard `INFO` level conventions.
- **INFO**:
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`):
    `mcp_worker_restart_scheduled instance_id=%s attempt=%d max_retries=%d`
    `delay_s=%.2f exitcode=%s reason=heartbeat_timeout`
    Logged when a heartbeat timeout triggers an automatic respawn attempt under active
    `McpWorkerRestartPolicy`.
- **DEBUG**:
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_heartbeat_pong instance_id=%s pid=%s latency_s=%.4f`
    Logged at DEBUG severity when a valid `HEARTBEAT_PONG` is received matching the expected nonce.
    Includes probe-to-pong elapsed roundtrip duration `latency_s` in seconds.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value ...`)
- Includes context: yes (`instance_id`, `pid`, `timeout_s`, `latency_s`, `expected`, `got`)
- Log levels: DEBUG, INFO, WARNING, ERROR (ERR)

### Secret Safety Verification

All heartbeat watchdog log events strictly avoid logging sensitive data:
1. **Opaque Nonces Only**: Heartbeat probes carry pseudo-random 16-character hex nonces
   (`uuid.uuid4().hex[:16]`). No user tokens, request payloads, tool parameters, or env secrets are
   involved.
2. **Metadata Context**: Log parameters are strictly limited to identifiers, process IDs, timing
   durations, and nonce strings.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Roundtrip Latency**: Measured per heartbeat roundtrip (`latency_s`), logged at DEBUG level for
  performance profiling and IPC overhead diagnostics.
- **Probe Overhead**: Minimal overhead ($O(1)$ IPC pipe write and poll per interval, default 2.0s).
- **Detection Boundedness**: Hung workers are detected and terminated within bounded delay
  (`timeout_s + loop_interval`, typically within 0.1s of timeout expiry).

### Business Metrics

Business metrics:
- `mcp_server_instances{state="failed"}`: Incremented by registry / supervisor when a worker fails
  due to an unrecoverable heartbeat timeout (exhausted retries or restart disabled).
- `mcp_server_instances{state="restarting"}`: Set during backoff delay before respawn.

### System Health Metrics

System health metrics:
- **Resource usage**: Watchdog termination prevents hung worker processes from indefinitely leaking
  RAM, CPU threads, open sockets, or file descriptors.
- **Component status**: Worker transitions to `failed` state with descriptive `last_error`
  indicating exact heartbeat timeout duration.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`mcp_server_instances{state="..."}`)
- [ ] Grafana dashboards (tracking heartbeat timeouts, worker restart rates, and roundtrip latency)
- [ ] Alerting rules (alert on repeated `mcp_worker_heartbeat_timeout` events for a server instance)
- [x] Log aggregation (structured key-value event streams for ELK, Loki, or Datadog)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`mcp_worker_heartbeat_timeout`, `mcp_worker_heartbeat_pong`,
  `mcp_worker_heartbeat_pong_mismatch`).
- [x] Metrics are collected correctly (worker states updated accurately in supervisor and registry).
- [x] Logging works in error scenarios (frozen workers, timeouts, nonce mismatches).
- [x] Large data structures are not logged (only metadata fields and identifiers emitted).
- [x] Metrics are available for monitoring.

## Notes

### Automated caplog Verification in `tests/test_mcp_ipc_heartbeat_watchdog_repro.py`

Automated test assertions using pytest's `caplog` fixture verify that:

1. **`test_normal_worker_heartbeats_roundtrip_successfully`**:
   - Asserts `mcp_worker_heartbeat_pong` is logged at `DEBUG` level.
   - Asserts context `instance_id=srv-hb-normal` and `latency_s=` are present.
   - Verifies normal running worker continues operating seamlessly.

2. **`test_hung_worker_times_out_and_is_terminated_to_failed`**:
   - Asserts `mcp_worker_heartbeat_timeout` is logged at `ERROR` level.
   - Asserts context `instance_id=srv-hb-hung`, `pid=...`, and `timeout_s=0.40` are present.
   - Verifies hung worker process is terminated and transitions to `failed` state.

3. **`test_disabled_watchdog_does_not_terminate_hung_worker`**:
   - Asserts absence of `mcp_worker_heartbeat_timeout` error logs when watchdog is disabled.
   - Verifies worker process remains alive and untouched.

4. **`test_heartbeat_timeout_interplay_with_auto_restart`**:
   - Asserts `mcp_worker_heartbeat_timeout` is logged at `ERROR` level.
   - Verifies auto-restart kicks in, supervisor respawns a new worker with a new PID, and
     server returns to `running` state.

5. **`test_heartbeat_pong_mismatch_warning_logged`**:
   - Asserts `mcp_worker_heartbeat_pong_mismatch` is logged at `WARNING` level.
   - Asserts context `instance_id`, `expected=...`, and `got=...` are present.
   - Verifies unexpected nonces do not corrupt supervisor pending heartbeat state.

### Operational Guidance

- When `mcp_worker_heartbeat_timeout` is logged:
  - Cause: MCP worker process event loop is completely blocked (CPU loop, blocking synchronous I/O,
    deadlock, or C-extension freeze).
  - Remediation: Inspect worker tool implementations for unhandled blocking calls. If worker tools
    perform long CPU-bound calculations, consider tuning `timeout_s` and `interval_s` via
    `McpHeartbeatPolicy` in settings.
- When `mcp_worker_heartbeat_pong_mismatch` is logged:
  - Cause: A delayed pong arrived after a previous timeout had already reset the pending nonce, or
    IPC messages arrived out of order.
  - Remediation: Check for IPC pipe saturation or system-wide scheduling latency spikes.
