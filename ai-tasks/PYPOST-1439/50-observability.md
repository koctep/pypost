# PYPOST-1439: Observability Implementation

## Logging Implementation

### Added Logs

Process-mode MCP isolation (spawn / STARTED|START_FAILED / unexpected exit→failed /
STOP→SIGTERM→SIGKILL / execution_mode). Extends existing `key=value` registry and supervisor
patterns; does not log variable snapshots, tool payloads, or other large structures.

- **EMERG**: N/A — child-process lifecycle failures stay within the host process and are not
  kernel/OS emergencies.
- **ALERT**: N/A — unexpected worker exits are contained per instance; peer servers keep serving.
- **CRIT**: N/A — stop escalation and start failures are recoverable via registry `failed` status.
- **ERR**:
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_start_failed instance_id=%s pid=%s error=%s` — IPC `START_FAILED` from the child.
  - `pypost/core/mcp_process_supervisor.py` (`_monitor_loop`):
    `mcp_worker_unexpected_exit instance_id=%s pid=%s exitcode=%s prior_state=%s` — child died
    while `starting` or `running` (before registry callback).
  - `pypost/core/mcp_server_registry.py` (`_on_worker_unexpected_exit`):
    `mcp_registry_unexpected_child_exit instance_id=%s port=%d exitcode=%s prior_state=%s` —
    host maps unexpected exit → `failed` (then `mcp_registry_status` + instance gauges).
  - `pypost/core/mcp_server_runner.py` (`ProcessServerRunner.start`):
    `mcp_process_runner_start_failed instance_id=%s error=%s` — spawn/wait raised before bind.
  - Existing: `mcp_worker_start_failed` / `mcp_worker_fatal` in `mcp_worker_process.py`;
    registry stop/teardown errors unchanged.
- **WARNING**:
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`):
    `mcp_worker_terminate instance_id=%s pid=%s signal=SIGTERM` — STOP join exceeded; escalate.
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`):
    `mcp_worker_kill instance_id=%s pid=%s signal=SIGKILL` — SIGTERM join exceeded; force kill.
  - Existing: debug-opcode reject / IPC reader / shutdown callback exceptions.
- **NOTICE**: N/A — operational lifecycle events use INFO under the project syslog mapping.
- **INFO**:
  - `pypost/core/mcp_server_registry.py` (`__init__`):
    `mcp_registry_execution_mode_selected execution_mode=%s` — `thread` vs `process` selection.
  - `pypost/core/mcp_server_registry.py` (`start`):
    `mcp_registry_start_requested ... execution_mode=%s` — start path includes mode.
  - `pypost/core/mcp_process_supervisor.py` (`spawn_worker`):
    `mcp_worker_spawned instance_id=%s pid=%s host=%s port=%d tool_count=%d` — child spawned
    (no variables/secrets logged).
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_started instance_id=%s pid=%s` — IPC `STARTED` (listening).
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`):
    `mcp_worker_stop_requested instance_id=%s pid=%s budget_s=%.3f` — IPC STOP before escalate.
  - `pypost/core/mcp_process_supervisor.py` (`stop_worker`):
    `mcp_worker_stop_finished instance_id=%s pid=%s alive=%s exitcode=%s` — stop outcome.
  - Existing: `mcp_registry_status` / stop / concurrent teardown INFO lines.
- **DEBUG**: Existing registry teardown worker and manager-start probes unchanged.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value`)
- Includes context: yes (`instance_id`, `pid`, `host`, `port`, `exitcode`, `execution_mode`,
  `prior_state`, `signal`, `budget_s`, `tool_count`; never variable maps or tool bodies)
- Log levels: DEBUG, INFO, WARNING, ERROR (ERR)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A for this step — no new histograms; process stop uses existing stop budget
  (~2s SIGTERM→SIGKILL) reflected in stop logs, not a new metric.
- **Throughput**: N/A — no new process-mode throughput instruments.
- **Error rate**: covered by `failed` gauge updates on unexpected exit / start failure (below).

### Business Metrics

Business metrics:
- Reused `mcp_server_instances{state=...}` via existing `_publish_instance_metrics` on every
  `_set_status` (including unexpected child exit → `failed`). No new Prometheus series for
  PYPOST-1439.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A new collectors — child RSS remains an evaluation/dev-doc concern.
- **Component status**: registry states `stopped` / `starting` / `running` / `failed` published
  through `MetricsTrackerProtocol.set_mcp_server_instance_counts`.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (existing `mcp_server_instances` gauge; process mode feeds same path)
- [ ] Grafana dashboards (no new panels required for this ticket)
- [ ] Alerting rules (operators can alert on `failed` count / unexpected-exit log signatures)
- [x] Log aggregation (syslog-compatible structured `key=value` events)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`key=value` event names aligned with registry/supervisor)
- [x] Metrics are collected correctly (status → `_publish_instance_metrics` on exit→failed)
- [x] Logging works in error scenarios (START_FAILED, unexpected exit, SIGTERM/SIGKILL escalate)
- [x] Large data structures are not logged (variables/hidden keys/tools omitted from spawn logs)
- [x] Metrics are available for monitoring (existing instance-count gauges)

## Notes

- Architecture Step 6: “status transitions for unexpected child exit; reuse
  `mcp_server_instance_counts`; structured logs for spawn/stop/kill.”
- `mcp_observability.py` remains inbound MCP argument-validation helpers (PYPOST-1100); process
  isolation observability lives on the registry/supervisor/runner loggers.
- Isolation suite: `make test PYTEST_ARGS="tests/test_mcp_process_isolation_repro.py"`.
