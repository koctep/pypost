# PYPOST-978: Observability Implementation

## Verdict

**N/A for new production observability.** This ticket is a test-only migration of
the golden e2e timeout companion to
`session.wait_for_text(..., in_current_tab=True)`. No `pypost/` package code,
logging schema, or metrics surface changed (NFR-4, AC-5).

Session wait diagnostics already exist on the path the companion now calls.
Adding duplicate production logs or counters would not improve triage for a
call-site style change.

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | Golden timeout companion in `tests/test_agent_golden_e2e.py`; AST convention guard in `tests/test_agent_e2e_response_panel.py` |
| Critical path | Forced near-zero text wait → `UiWaitTimeoutError` rewrap → pytest asserts `step` / `response_excerpt` |
| Production product logging | Unchanged — companion consumes existing `AgentAppSession.wait_for_text` → `pypost.agent.ui_wait` |
| Performance / business metrics | Not applicable — CI harness only |
| Parent contracts | PYPOST-949 session tab-scoped waits; PYPOST-950 golden timeout diagnostics |

## Logging Implementation

### Added Logs

None. No production or harness logger calls were added in this task.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: N/A — no new
  operational signals
- **DEBUG**: reuse existing `pypost.agent.ui_wait` events (below); no new events

### Existing diagnostics (unchanged, now used by companion)

Session `wait_for_text` delegates to free-function `wait_for_text` under
`_action_root(in_current_tab=…)`, which polls via `wait_until`:

| Event | Level | Logger | Fields |
| ----- | ----- | ------ | ------ |
| `ui_wait_settled` | DEBUG | `pypost.agent.ui_wait` | `condition`, `waited_ms`, `timeout_s` |
| `ui_wait_timeout` | DEBUG | `pypost.agent.ui_wait` | `condition`, `waited_ms`, `timeout_s` |

On timeout, `UiWaitTimeoutError.diagnostics` still carries scalar wait context
(`widget_id`, text mismatch fields, `timeout_s`, `condition`) regardless of
search root (window vs current tab). No `in_current_tab` log field was added in
PYPOST-949; that decision remains correct here.

### Harness observability (test path)

The companion
`test_agent_golden_settle_timeout_includes_step_and_excerpt` keeps the
PYPOST-950 rewrap contract after the call-site migration:

| Field | Source | Purpose |
| ----- | ------ | ------- |
| `step` | Companion rewrap | `wait_response_after_send` triage fingerprint |
| `response_excerpt` | `response_panel_excerpt(session.ui_snapshot())` | Compact panel context at timeout |
| `widget_id` / `expected` | Underlying `UiWaitTimeoutError.diagnostics` | Identity of the missed wait |

These fields surface in `UiWaitTimeoutError.diagnostics` and pytest failure
output — not as new syslog events.

### Log Structure

- Structured logs: yes (existing `event key=value` DEBUG lines in `ui_wait`)
- Includes context: yes — timing scalars + condition name; rich dialog context
  stays on the exception, not duplicated into logs
- Log levels used by this path: DEBUG only (pre-existing)
- Large payloads: not logged (excerpts / clipped text on exception only)

## Metrics Implementation (if applicable)

### Performance Metrics

None. Existing DEBUG `waited_ms` / `timeout_s` remain sufficient for
per-occurrence diagnosis. Module wall-clock is bounded by
`pytest.mark.timeout(60)` on the golden module.

### Business Metrics

None — no user transaction or product-behaviour change.

### System Health Metrics

None — agent metrics server and health behaviour unchanged.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (unchanged product surface)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A (DEBUG wait timeouts are diagnostic, not paging)
- [ ] Log aggregation — N/A for new sinks; existing `ui_wait_*` events remain
  greppable in the documented event-first format

## Validation Results

Validation results:

- [x] No new application logs required for this test-only call-site migration
- [x] Existing session wait DEBUG events cover settle success/timeout
- [x] Companion still asserts `step`, `response_excerpt`, `widget_id`, `expected`
- [x] Large data structures are not logged (unchanged `ui_wait` contract)
- [x] Metrics applicability assessed — none warranted (NFR-4)

No separate Step 6 test run was required: Step 5 already recorded scoped green
proofs for the golden module and the convention guard. Observability behaviour
is identical to pre-migration for the same forced-timeout scenario; only the
wait entrypoint style changed.

## Notes

- Decision: **document existing diagnostics; add no new production
  instrumentation.**
- Deliberately not added (same rationale as PYPOST-949):
  - Log field for `in_current_tab` — boolean inferable from session state
  - Metrics counter for tab-scoped / golden waits — low-volume test path
- Timeout-diagnostics lock alignment remains owned by PYPOST-950 (excluded from
  this ticket); this migration preserves that companion’s assert surface.
- Observability is ready for production for the PYPOST-978 scope: the necessary
  DEBUG events and exception diagnostics already exist; the golden companion
  continues to prove the harness timeout contract via the preferred session API.
