# PYPOST-934: Observability Implementation

Test-only debt: production dialog-settle timeout rewrap and modal scalars were
delivered in [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919). This
story adds **automated regression coverage** for that failure-path contract — no
new production loggers, metrics, or exception shapes.

## Logging Implementation

### Added Logs

None. The companion reuses sibling agent DEBUG/INFO events from the existing
`agent_e2e` session and the same `wait_until` stack as the happy-path proof.

- **EMERG / ALERT / CRIT / ERR / NOTICE**: none added.
- **WARNING**: none added — ready-timeout WARNING remains on
  `AgentAppSession` (PYPOST-833) if launch never becomes ready.
- **INFO**: none added — lifecycle `agent_session_*` events fire unchanged.
- **DEBUG** (reused from PYPOST-837 / PYPOST-919):
  - `pypost.agent.ui_wait` — `ui_wait_settled` / `ui_wait_timeout` with
    `condition`, `waited_ms`, `timeout_s` (never dialog bodies or widget trees).
  - Sibling stack unchanged: `ui_action_applied` on
    `ui_click(SETTINGS_BUTTON)`, optional snapshot events if other paths run.

### Existing failure diagnostics (already covered — PYPOST-919)

Dialog-settle diagnosability lives on the **exception path**, not in new
application logs. PYPOST-919 defined the contract; PYPOST-934 locks it in CI.

| Failure | Diagnostic carrier |
| --- | --- |
| Dialog settle budget expires | Rewrapped `UiWaitTimeoutError` with |
| | `diagnostics["step"]="wait_dialog_after_settings_open"`, |
| | inner `condition` / `timeout_s`, plus scalars |
| | `dialog_title` and `active_modal_type` from `_modal_diag()` |
| | (title string / type name or `None` if no modal) |
| Missing Settings control | `UiTargetNotFoundError` from |
| | `find_widget` / `ui_click` (sibling actions) |
| Ready never happens | Existing lifecycle timeout / |
| | `agent_session_ready_timeout` |
| Forced-timeout callback error | Re-raised from `settle_error` after |
| | `ui_click` returns (modal always `reject()` in `finally`) |

Stable names used by the scenario:

| Name | Value | Role |
| --- | --- | --- |
| Wait step | `wait_dialog_after_settings_open` | `SETTLE_STEP` on timeout |
| | | rewrap (`diagnostics["step"]`) |
| Happy condition | `settings_dialog_present` | Happy-path `condition_name` |
| Forced condition | `forced_dialog_settle_timeout` | Companion `condition_name` |
| Happy settle budget | `DIALOG_SETTLE_TIMEOUT_S` (10 s) | Happy-path `wait_until` |
| Forced settle budget | `FORCED_SETTLE_TIMEOUT_S` (0.05 s) | Deterministic timeout |
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

Diagnostics for dialog-settle failure-path correctness:

- Exception path: `UiWaitTimeoutError.diagnostics` enriched in
  `tests/test_agent_dialog_settle_e2e.py` (happy-path rewrap unchanged;
  companion mirrors the same rewrap block)
- Automated regression: `test_agent_dialog_settle_timeout_includes_step_and_modal_diag`
  asserts `step`, `dialog_title`, and `active_modal_type` keys on forced
  timeout (FR3, FR4)
- Manual: `make test-agent-e2e` (or scoped
  `PYTEST_ARGS="tests/test_agent_dialog_settle_e2e.py -v"`); enable DEBUG
  to see `ui_wait_timeout` with `condition=forced_dialog_settle_timeout`

## Metrics Implementation (if applicable)

### Performance Metrics

**N/A — no new metrics.** Wait duration remains sibling DEBUG `waited_ms` on
`ui_wait_settled` / `ui_wait_timeout`. Agent sessions keep ephemeral metrics
ports (PYPOST-833); the companion does not scrape or assert metrics.

### Business Metrics

None.

### System Health Metrics

None new. CI boundedness is enforced by near-zero forced `wait_until` budget +
module `pytest.mark.timeout(60)` + fail-closed modal `reject()`.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable (test/composition coverage)
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_agent_dialog_settle_e2e.py` (2 tests) under
  `make test-agent-e2e` (offscreen)
- [x] Log aggregation — reused sibling DEBUG/INFO events follow
  `event_name key=value`

## Validation Results

Validation results:
- [x] Logs are correctly formatted — no new events; siblings already
  validated (PYPOST-837 / logging catalog)
- [x] Metrics are collected correctly — N/A (no new metrics)
- [x] Logging works in error scenarios — forced-timeout companion asserts
  `step=wait_dialog_after_settings_open` + modal scalar keys; DEBUG
  `ui_wait_timeout` still fires from `wait_until` inside the timer callback
- [x] Large data structures are not logged — no trees / dialog bodies;
  diagnostics are scalars only
- [x] Metrics are available for monitoring — N/A

### Companion test coverage (`tests/test_agent_dialog_settle_e2e.py`)

**`test_agent_dialog_settle_timeout_includes_step_and_modal_diag`**

- Forces dialog-settle timeout via `wait_until(lambda: False, timeout=0.05)`
  inside the modal-safe `QTimer.singleShot` callback (same architecture as
  happy path; golden Send companion precedent).
- Mirrors PYPOST-919 rewrap: `step=SETTLE_STEP` and `**_modal_diag()`.
- Asserts `diagnostics["step"] == SETTLE_STEP` and presence of
  `dialog_title` / `active_modal_type` (values may be `None` or
  Settings-scoped strings/types — membership only, matching golden
  `response_excerpt` pattern).

**`test_agent_dialog_settle_after_settings_open`** (PYPOST-919 — unchanged)

- Happy-path settle; timeout rewrap block remains the production contract
  source for the companion mirror.

## Gaps and Confirmations

**Confirmed — no new production observability needed:**

- Requirements and architecture mark production API / log / metric changes out
  of scope; acceptance is test-only assertion of existing diagnostics.
- PYPOST-919 already ships the timeout rewrap and modal scalar contract on
  the happy-path timer callback.

**Gap closed by PYPOST-934:**

- **Coverage gap (PYPOST-919 TD-1):** failure-path step + modal scalars were
  implemented but not regression-tested. The companion closes this — parity
  with golden Send forced-timeout companion (`test_agent_golden_settle_timeout_includes_step_and_excerpt`).

**Known limitations (not observability gaps for PYPOST-934):**

- Companion asserts scalar **key presence**, not specific title/type values
  (by design; modal may or may not be open when the near-zero budget expires).
- No `caplog` assertion on DEBUG `ui_wait_timeout` — exception diagnostics
  are the primary failure signal (same posture as PYPOST-838 / golden
  companion).
- Inline rewrap duplication in happy + companion callbacks — shared helper
  deferred to PYPOST-936.
- `SETTINGS_DIALOG` widget identity hardening — PYPOST-935 (separate debt).

## Notes

Same posture as PYPOST-919 / PYPOST-838: DEBUG scalars from the agent wait
stack, actionable `UiWaitTimeoutError` for callers, CI as the primary gate.
New production metrics or log events are **N/A** — this story validates
existing failure diagnosability under `make test-agent-e2e`.

Discoverability: module already listed in `doc/dev/agent_e2e.md` (PYPOST-919);
logging catalog lists `ui_wait_*` from PYPOST-837. Cross-reference:
`ai-tasks/PYPOST-919/50-observability.md` for the parent observability
contract.
