# PYPOST-836: Observability Implementation

## Logging Implementation

### Added Logs

UI actions are on-demand harness APIs. Typed text and selection values must never
be logged. Primary proof remains the CI/test gate; DEBUG scalars give operators
duration without dumping secrets from filled fields.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: none added —
  action failures raise `UiTargetNotFoundError` / `UiTargetNotInteractableError`
  to the caller (actionable errors); they are not lifecycle control paths.
- **DEBUG**:
  - `pypost.agent.ui_actions` — `ui_action_applied` after a successful
    primitive (`primitive`, `widget_id`, `outcome=ok`, `duration_ms`). Scalars
    only; never fill text, option labels, or key payloads.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (primitive name, widget id, duration only)
- Log levels: DEBUG

Diagnostics for action correctness:

- Automated: `tests/test_ui_actions.py` — each primitive + missing/not-interactable
  + main-window subset via `AgentAppSession`
- Manual: call primitives after `is_ui_ready` and assert widget state / snapshot

## Metrics Implementation (if applicable)

### Performance Metrics

No Prometheus / OTel instruments. Action duration is logged as `duration_ms` on
the DEBUG event above. Agent sessions bind an ephemeral metrics port
(PYPOST-833), so scrapeable counters would not outlive the session.

### Business Metrics

None. Actions are a harness/drive contract, not a user-product KPI.

### System Health Metrics

None new.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for ephemeral agent sessions
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_ui_actions.py` under `make test` (offscreen)
- [x] Log aggregation — DEBUG event follows `event_name key=value` convention
  (`doc/dev/logging.md`); catalog entry in Step 7

## Validation Results

Validation results:
- [x] Logs are correctly formatted — `ui_action_applied primitive=… widget_id=…`
- [x] Metrics are collected correctly — N/A (DEBUG duration only)
- [x] Logging works in error scenarios — errors raise exceptions; no noisy
  ERROR logs for expected missing targets
- [x] Large data structures are not logged — no text/option payloads
- [x] Metrics are available for monitoring — N/A

## Notes

Same observability posture as PYPOST-835 snapshot: DEBUG success summary, no
agent-visible secret material in logs, CI as the primary gate.
