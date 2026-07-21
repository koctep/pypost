# PYPOST-833: Observability Implementation

## Logging Implementation

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR** (via `logger.exception`):
  - `pypost.agent.lifecycle` — `agent_session_mcp_stop_failed` on MCP stop errors
  - `pypost.agent.lifecycle` — `agent_session_handle_exit_failed` on exit errors
  - `pypost.agent.lifecycle` — `agent_session_window_close_failed` on close errors
  - `pypost.agent.lifecycle` — `agent_session_metrics_stop_failed` on metrics stop
  - `pypost.agent.lifecycle` — `agent_session_temp_cleanup_failed` on temp dir cleanup
- **WARNING**:
  - `pypost.agent.lifecycle` — `agent_session_ready_timeout` when
    `MainWindow.is_ui_ready` is not true within `ready_timeout`
    (`ready_timeout_s`, `waited_ms`, `metrics_port`); shutdown still runs
- **NOTICE**: none (stdlib logging has no NOTICE; significant events use INFO)
- **INFO**:
  - `pypost.agent.lifecycle` — `agent_session_started` at launch
    (`offscreen`, `ready_timeout_s`, `metrics_port`, `config_dir`, `data_dir`)
  - `pypost.agent.lifecycle` — `agent_session_ready` after ready gate
    (`ready_ms`, `launch_ms`, `metrics_port`)
  - `pypost.agent.lifecycle` — `agent_session_shutdown_started`
    (`metrics_port`, `started`)
  - `pypost.agent.lifecycle` — `agent_session_shutdown_completed`
    (`shutdown_ms`, `metrics_port`)
  - `pypost.ui.main_window` — `main_window_ui_ready` when startup restore gate
    sets `is_ui_ready` (interactive and agent paths)
- **DEBUG**: none added

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (timeouts, durations, metrics port, isolation dirs)
- Log levels: INFO, WARNING, ERROR (via `logger.exception`)

## Metrics Implementation (if applicable)

### Performance Metrics

No Prometheus / OTel instruments added for agent lifecycle.

Durations are logged as `ready_ms`, `launch_ms`, and `shutdown_ms` on the
session events above. Agent sessions bind an **ephemeral** metrics port that is
stopped at shutdown, so scrapeable counters would not outlive the session.

### Business Metrics

None. Lifecycle is a harness contract, not a user-product action.

### System Health Metrics

None new. Session shutdown still stops the ephemeral metrics server and MCP
(if running); failures are logged with `_failed` events.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for ephemeral agent sessions
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — events follow project `event_name key=value` convention
  for grep/CI allowlists (`doc/dev/logging.md`)

## Validation Results

Validation results:
- [x] Logs use `%` formatting and snake_case event names
- [x] Timeout path logs WARNING then still attempts shutdown
- [x] Large data structures are not logged (paths and scalars only)
- [x] Smoke test still passes launch → ready → shutdown
- [x] Catalog entry in `doc/dev/logging.md` — completed in Step 7 (Dev Docs)

## Notes

- Renamed earlier Step 3 events for outcome suffixes:
  `agent_session_start` → `agent_session_started`,
  `agent_session_shutdown` → `agent_session_shutdown_started`,
  `agent_session_shutdown_complete` → `agent_session_shutdown_completed`.
- `main_window_ui_ready` is the production-surface signal that the ready
  condition FR3 polls; `agent_session_ready` is the harness confirmation after
  the wait succeeds.
- Full metrics registry expansion is deferred unless a sibling needs scrapeable
  agent-session counters across long-lived processes.
