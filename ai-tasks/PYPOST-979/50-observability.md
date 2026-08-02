# PYPOST-979: Observability Implementation

## Scope

**TEST-ONLY.** Multi-tab characterizing proofs for tab-scoped session
`wait_for_widget` / `wait_for_enabled`. No production code, logging schema, or
metric changes (requirements DoD).

Existing wait helpers already emit timeout diagnostics; this task only asserts
scoping via pytest (`UiWaitTimeoutError` on isolation failure, identity on
success). Parent tab-scoped wait observability:
[PYPOST-949/50-observability.md](../PYPOST-949/50-observability.md).

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | Session `wait_for_widget` / `wait_for_enabled` with `in_current_tab=True` |
| Critical path | Multi-tab fixture → tab-scoped wait → identity or forced timeout |
| Production product logging | N/A — tests only |
| Metrics | N/A — pytest harness |
| Existing diagnostics | `UiWaitTimeoutError.diagnostics` + DEBUG `ui_wait_*` (unchanged) |

## Logging Implementation

### Added Logs

None. Reuse existing `pypost.agent.ui_wait` poll-loop signals (DEBUG):

| Event | When | Fields |
| --- | --- | --- |
| `ui_wait_settled` | Condition met | timing scalars, condition name |
| `ui_wait_timeout` | Budget exhausted | timing scalars; message carries diagnostic key=value pairs |

`UiWaitTimeoutError.diagnostics` still carries scalars such as `widget_id`,
`found`, and enabled/text mismatch fields regardless of search root (window vs
current tab). No `in_current_tab` log field (same deliberate omission as
PYPOST-949).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none (isolation timeouts are caught by pytest; not new log lines)
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none new
- **DEBUG**: reuse `ui_wait_settled` / `ui_wait_timeout` only

### Log Structure

- Structured logs: yes (existing tokenized DEBUG lines)
- Includes context: timing scalars + condition name; diagnostics on exception
- Log levels: DEBUG only for wait settle/timeout (unchanged)

## Harness observability (test path)

Multi-tab proofs in `tests/test_ui_wait.py` use existing timeout carriers — no
extra wrappers or logging in tests:

| Test | Observability signal |
| --- | --- |
| `test_session_wait_for_widget_in_current_tab_multi_tab` | Tab-scoped success returns active-tab widget; rename active id → tab-scoped raises `UiWaitTimeoutError`; window-scoped still finds background duplicate |
| `test_session_wait_for_enabled_in_current_tab_multi_tab` | Disable active only → tab-scoped raises `UiWaitTimeoutError`; re-enable → identity under active tab |

Forced isolation budgets use short `timeout=0.5` so CI failures surface quickly
with the existing exception message / `diagnostics` dict. Module bound by
`pytest.mark.timeout(60)`.

## Metrics Implementation (if applicable)

### Performance Metrics

None.

### Business Metrics

None.

### System Health Metrics

None.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation — not applicable for this task (DEBUG wait events already
  documented in `doc/dev/ui_wait.md` / `doc/dev/logging.md`)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (no new events; existing `ui_wait_*`)
- [x] Metrics are collected correctly (N/A)
- [x] Isolation paths raise `UiWaitTimeoutError` with existing diagnostics
- [x] Large data structures are not logged (scalars / short strings only)
- [x] Metrics are available for monitoring (N/A)

## Notes

Decision: **no new instrumentation.** Observability for PYPOST-979 is the
characterizing proofs themselves — they lock that background-tab duplicates
cannot satisfy tab-scoped widget/enabled waits, relying on the same timeout
diagnostics shipped with the wait helpers.

Deliberately not added:

- Log field for `in_current_tab` — boolean; inferable from session state when
  debugging (PYPOST-949 decision)
- Metrics counter for tab-scoped waits — low-volume test/harness path
- Extra logging inside the multi-tab tests — noise without CI signal
