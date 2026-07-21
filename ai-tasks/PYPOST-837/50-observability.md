# PYPOST-837: Observability Implementation

## Logging Implementation

### Added Logs

Settle waits are on-demand harness APIs. Snapshot trees and widget text values
must not be dumped on success. Timeout diagnostics are carried on
`UiWaitTimeoutError` for callers; DEBUG logs only scalars.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: none added —
  wait failures raise `UiWaitTimeoutError` to the caller; ready-timeout WARNING
  on `AgentAppSession` is unchanged from PYPOST-833.
- **DEBUG**:
  - `pypost.agent.ui_wait` — `ui_wait_settled` after a successful wait
    (`condition`, `waited_ms`, `timeout_s`).
  - `pypost.agent.ui_wait` — `ui_wait_timeout` when the budget expires
    (`condition`, `waited_ms`, `timeout_s`). No tree or full text payloads.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (condition name, timing scalars only)
- Log levels: DEBUG

Diagnostics for wait correctness:

- Exception path: `UiWaitTimeoutError.diagnostics` (widget_id, found/visible/
  enabled, clipped actual_text, snapshot node counts — never full trees)
- Automated: `tests/test_ui_wait.py`
- Manual: wait after action; inspect exception message / diagnostics on failure

## Metrics Implementation (if applicable)

### Performance Metrics

No Prometheus / OTel instruments. Wait duration is logged as `waited_ms` on the
DEBUG events above. Agent sessions use ephemeral metrics ports (PYPOST-833).

### Business Metrics

None.

### System Health Metrics

None new.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for ephemeral agent sessions
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_ui_wait.py` under `make test` (offscreen)
- [x] Log aggregation — DEBUG events follow `event_name key=value`

## Validation Results

Validation results:
- [x] Logs are correctly formatted — `ui_wait_settled` / `ui_wait_timeout`
- [x] Metrics are collected correctly — N/A (DEBUG duration only)
- [x] Logging works in error scenarios — timeout raises; DEBUG timeout event
- [x] Large data structures are not logged — no snapshot trees / full text
- [x] Metrics are available for monitoring — N/A

## Notes

Same posture as snapshot/actions: DEBUG scalars, actionable exceptions for
callers, CI as the primary gate.
