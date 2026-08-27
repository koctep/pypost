# PYPOST-1178: Observability Implementation

## Scope

Stabilize MCP server-manager restart after exposed-tool-set changes by landing
`_wait_until_port_bindable` (bounded probe-bind between `stop_server` and
`start_server`) plus test port helpers. Observability for this path is the
existing deadline WARNING plus reuse of the restart lifecycle logs already on
`MCPServerManager`. Test helpers under `tests/helpers/` do not log (CI asserts
and pytest output remain the failure surface).

## Logging Implementation

### Added Logs

No new log calls in this step. Production already emits the deadline warning
required by architecture; happy-path readiness is silent (early return after
successful probe-bind).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none new — bind/start failure after a busy deadline still surfaces via
  existing `mcp_server_start_failed` (`logger.error` / `logger.exception` in
  `pypost/core/qt/mcp_server.py`)
- **WARNING** (existing — primary observable for this task):
  - `MCPServerManager._wait_until_port_bindable`
    (`pypost/core/qt/mcp_server.py`):
    `mcp_port_still_busy host=%s port=%d` — emitted once when the monotonic
    deadline elapses while the configured host/port still cannot be probe-bound
    (or the prior thread is still reported running). Method returns `None` and
    `update_tools` proceeds to `start_server`; subsequent failure remains visible
    via `start_failed` / ERROR logs.
- **NOTICE**: none (Python `logging` has no NOTICE level)
- **INFO** (existing — restart lifecycle context, unchanged):
  - `update_tools`: `mcp_tools_changed tool_count=%d restarting=true`
  - `stop_server`: `MCP server stopped`
  - `_notify_started`: `mcp_server_listening host=%s port=%d`
- **DEBUG**: none new for the wait gate (poll loops must not spam DEBUG every
  50ms)

Test-only helpers (`tests/helpers/port_allocation.py`,
`tests/helpers/mcp_live_server.py`) add no application logging.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event name then `key=value` fields for
  `mcp_port_still_busy` / sibling MCP manager events)
- Includes context: yes (`host`, `port` on the busy-port WARNING; tool count on
  tools-changed INFO)
- Log levels: WARNING (deadline still busy), INFO (restart lifecycle), ERROR
  (start failure — pre-existing)
- Payload fields: host/port only on the wait timeout; no socket dumps, no full
  tool payloads, no large structures

## Metrics Implementation (if applicable)

No new metrics. Port readiness is a bounded local wait, not a Prometheus
dimension. Failure rate stays observable via existing ERROR logs /
`start_failed` signal.

### Performance Metrics

Added performance metrics:

- **Response time**: none — wait timeout is a fixed default (5.0s), not a
  histogram series
- **Throughput**: none
- **Error rate**: none new — rely on `mcp_server_start_failed` when start fails
  after a still-busy port

### Business Metrics

Business metrics:

- none — restart readiness is infrastructure reliability, not a conversion event

### System Health Metrics

System health metrics:

- **Resource usage**: N/A — not in scope
- **Component status**: MCP manager restart health remains covered by
  `mcp_port_still_busy` (WARNING) then `mcp_server_listening` (INFO) or
  `mcp_server_start_failed` (ERROR)

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable for this debt item
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — optional future: alert on sustained
      `mcp_port_still_busy` volume; not required to close PYPOST-1178
- [x] Log aggregation (ELK, Loki, etc.) — logger
      `pypost.core.qt.mcp_server` already emits structured WARNING/INFO/ERROR
      on the restart path

Catalog updates for `doc/dev/logging.md` (if any) belong to Step 8, not this
step.

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`mcp_port_still_busy host=%s port=%d`)
- [x] Metrics are collected correctly — N/A; no new metrics
- [x] Logging works in error scenarios — deadline WARNING then existing start
      ERROR / `start_failed` if bind still fails
- [x] Large data structures are not logged — host/port and tool_count only
- [x] Metrics are available for monitoring — N/A; no new metrics
- [x] Happy path does not emit `mcp_port_still_busy` (early return on successful
      probe-bind; covered by restart readiness tests)

## Notes

- Architecture contract: `_wait_until_port_bindable(...) -> None` always;
  success = silent early return; timeout = WARNING then continue. Do not add a
  success INFO for every wait — that would noise the restart path.
- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not mark
  `[x]`.
