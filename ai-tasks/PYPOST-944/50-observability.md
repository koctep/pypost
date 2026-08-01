# PYPOST-944: Observability Implementation

## Scope

Test-only coverage task — no production logging or metrics changes. Opt-in fill
already emits DEBUG `ui_action_applied` with `via_key_clicks=true`
(`pypost/agent/ui_actions.py`, PYPOST-917); Step 4 added symmetric caplog
proof only.

## Logging Implementation

### Added Logs

No new log statements — test-only task.

Existing production observability for the path under test:

- **DEBUG** `ui_action_applied` on successful `ui_fill` with scalar
  `via_key_clicks=true|false` (lowercase); fill **text is never logged**
  (PYPOST-851 / NFR3).
- Logger: `pypost.agent.ui_actions`.

### Log Structure

- Structured logs: existing DEBUG scalar shape unchanged
- Includes context: `primitive=fill`, `widget_id`, `outcome=ok`, `duration_ms`,
  `via_key_clicks`
- Log levels: none added

## Metrics Implementation

Not applicable — test-only task; no metrics changes.

### Performance Metrics

N/A

### Business Metrics

N/A

### System Health Metrics

N/A

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

## Validation Results

- [x] No new logs required — existing DEBUG contract covered by Step 4 caplog
- [x] Metrics N/A
- [x] CI failure output remains actionable — parametrized caplog asserts scalar
  and absence of fill text on both fill modes
- [x] Large data structures are not logged — fill text absent from caplog
  (asserted)
- [x] N/A for production observability documented

## Notes

- `test_ui_action_applied_caplog` now parametrizes `(False, "false")` and
  `(True, "true")` — one caplog pattern, both fill modes (FR5).
- Behavioral keyClicks tests (`test_ui_fill_via_key_clicks_on_fixture`,
  `test_ui_fill_via_key_clicks_session`) remain the functional proof; caplog
  locks the DEBUG scalar contract.

## Self-Review (50-observability.mdc)

- [x] Key path covered by existing structured DEBUG event
- [x] No large payloads / fill text in logs
- [x] Documented in this file
