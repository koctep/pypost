# PYPOST-919: Observability Implementation

## Logging Implementation

### Added Logs

This story is a **test-only composition proof**
(`tests/test_agent_dialog_settle_e2e.py`). No new production loggers or events
were added. The dialog-settle run reuses sibling agent DEBUG/INFO events and
surfaces failure context on `UiWaitTimeoutError` (FR3), not via new syslog
streams.

- **EMERG / ALERT / CRIT / ERR / NOTICE**: none added.
- **WARNING**: none added — ready-timeout WARNING remains on
  `AgentAppSession` (PYPOST-833) if launch never becomes ready.
- **INFO**: none added — lifecycle session start/ready/shutdown events from
  PYPOST-833 fire unchanged during the agent_e2e session.
- **DEBUG** (reused, not redefined — from PYPOST-837):
  - `pypost.agent.ui_wait` — `ui_wait_settled` after successful
    `wait_until` (`condition=settings_dialog_present`, `waited_ms`,
    `timeout_s`).
  - `pypost.agent.ui_wait` — `ui_wait_timeout` when the settle budget
    expires (same scalar keys; never dialog content / widget trees).
  - Sibling stack unchanged: `agent_session_*`, `ui_action_applied` (on
    `ui_click(SETTINGS_BUTTON)`), optional snapshot events if other paths
    run.

### Failure diagnostics (primary observability for this story)

Dialog-settle diagnosability lives on the **exception path**, not in new
application logs:

| Failure | Diagnostic carrier |
| --- | --- |
| Dialog never appears within budget | Rewrapped `UiWaitTimeoutError` with |
| | `diagnostics["step"]="wait_dialog_after_settings_open"`, |
| | `condition` / `timeout_s` from the inner wait, plus scalars |
| | `dialog_title` and `active_modal_type` from `_modal_diag()` |
| | (title string / type name or `None` if no modal) |
| Missing Settings control | `UiTargetNotFoundError` from |
| | `find_widget` / `ui_click` (sibling actions) |
| Ready never happens | Existing lifecycle timeout / |
| | `agent_session_ready_timeout` |
| Settle callback error before assert | Re-raised from `settle_error` after |
| | `ui_click` returns (modal always `reject()` in `finally`) |

Stable names used by the scenario:

| Name | Value | Role |
| --- | --- | --- |
| Wait step | `wait_dialog_after_settings_open` | `SETTLE_STEP` on timeout |
| | | rewrap (`diagnostics["step"]`) |
| Condition | `settings_dialog_present` | `condition_name` for |
| | | `ui_wait_*` DEBUG + `UiWaitTimeoutError.condition` |
| Settle budget | `DIALOG_SETTLE_TIMEOUT_S` (10 s) | Bound for `wait_until` |
| Module budget | `@pytest.mark.timeout(60)` | Wall-clock hang guard |

No full snapshot trees, dialog field dumps, or large payloads are logged on
success or timeout — only scalar diagnostics.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`) —
  sibling agent modules only
- Includes context: yes (`condition` / timing on DEBUG; `step` + modal
  scalars on wait-timeout exception)
- Log levels: INFO / WARNING / DEBUG from siblings; no new levels from this
  story

Diagnostics for dialog-settle correctness:

- Exception path: `UiWaitTimeoutError.diagnostics` enriched in
  `tests/test_agent_dialog_settle_e2e.py`
- Automated: `tests/test_agent_dialog_settle_e2e.py` (`agent_e2e`)
- Manual: `make test-agent-e2e` (or scoped
  `PYTEST_ARGS="tests/test_agent_dialog_settle_e2e.py -v"`); enable DEBUG
  to see `ui_wait_settled` / `ui_wait_timeout` with
  `condition=settings_dialog_present`

## Metrics Implementation (if applicable)

### Performance Metrics

**N/A — no new metrics.** Wait duration remains sibling DEBUG `waited_ms` on
`ui_wait_settled` / `ui_wait_timeout`. Agent sessions keep ephemeral metrics
ports (PYPOST-833); the dialog-settle test does not scrape or assert metrics.
Prometheus / OTel instruments for a composition e2e proof would invent signal
without a production consumer.

### Business Metrics

None.

### System Health Metrics

None new. CI boundedness is enforced by `wait_until` timeout + module
`pytest.mark.timeout(60)` + fail-closed modal `reject()`.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable (test/composition coverage)
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_agent_dialog_settle_e2e.py` under
  `make test-agent-e2e` (offscreen)
- [x] Log aggregation — reused sibling DEBUG/INFO events follow
  `event_name key=value`

## Validation Results

Validation results:
- [x] Logs are correctly formatted — no new events; siblings already
  validated (PYPOST-837 / logging catalog)
- [x] Metrics are collected correctly — N/A (no new metrics)
- [x] Logging works in error scenarios — wait timeout rewrap carries
  `step=wait_dialog_after_settings_open` + modal scalars; DEBUG
  `ui_wait_timeout` still fires from `wait_until`
- [x] Large data structures are not logged — no trees / dialog bodies;
  diagnostics are scalars only
- [x] Metrics are available for monitoring — N/A

## Notes

Same posture as PYPOST-838 (golden Send): DEBUG scalars from the agent wait
stack, actionable `UiWaitTimeoutError` for callers, CI as the primary gate.
New production metrics or log events are **N/A** for this composition proof —
reuse of `ui_wait_settled` / `ui_wait_timeout` plus the step-named timeout
rewrap satisfies FR3.

Discoverability: harness table / cross-links in `doc/dev/agent_e2e.md`,
`agent_golden_e2e.md`, and `ui_wait.md` (Step 4); logging catalog already
lists `ui_wait_*` from PYPOST-837.
