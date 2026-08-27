# PYPOST-1180: Observability Implementation

## Verdict

**N/A — no new production observability.** This task is verification debt:
hermetic unit proofs of `NewTabProtocolPicker.prompt` outcomes (HTTP,
WebSocket, dismiss) in `tests/test_new_tab_protocol_picker.py` only. Step 4
confirmed production is a **no-op** (`pypost/ui/widgets/new_tab_protocol_picker.py`
unchanged). There is no new runtime path to log or meter.

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components changed | Test-only: shared `_install_fake_exec` and hermetic `prompt()` mapping proofs for `actions()[0]`, `actions()[1]`, and dismiss `None` |
| Critical production paths | Unchanged — picker → `TabProtocol \| None` mapping and presenter blank-tab routing remain as shipped in PYPOST-1157 |
| Performance / business metrics | Not applicable — no new user-facing or service behavior under load |

Product observability for blank-tab protocol choice (presenter INFO logs and
`gui_new_tab_actions_total`) was delivered under PYPOST-1157 and is outside
this debt item’s change set. CI regression signal for this ticket is the
green hermetic picker tests themselves, not new runtime telemetry.

## Logging Implementation

### Added Logs

No production logs added.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

Existing PYPOST-1157 presenter logs (`new_tab_action_triggered`,
`new_tab_action_cancelled`, `new_tab_action_completed`) remain unchanged and
are not exercised by these unit proofs (tests call `prompt()` with a mocked
`menu.exec`, not full presenter routing).

### Log Structure

Log format used:

- Structured logs: N/A (no new logs)
- Includes context: N/A
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A

### Business Metrics

Business metrics:

- N/A — no production request/session volume or conversion paths changed.
  Existing `gui_new_tab_actions_total{source, protocol}` from PYPOST-1157 is
  unchanged and out of scope (requirements explicitly exclude presenter
  metrics work).

### System Health Metrics

System health metrics:

- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation (ELK, Loki, etc.) — not applicable

## Validation Results

Validation results:

- [x] No new production logs required (scope confirmed: test-only / production no-op)
- [x] No new metrics required
- [x] Large data structures are not logged (nothing added)
- [x] Existing production observability left unchanged
- [ ] Metrics are available for monitoring — N/A for this task
- [ ] Logs are correctly formatted — N/A (none added)
- [ ] Logging works in error scenarios — N/A (none added)

## Notes

- Scope evidence: Steps 3–5 changed only
  `tests/test_new_tab_protocol_picker.py` (plus task artifacts); production
  picker module was inspected and left untouched.
- Suite reliability signal for FR-1..3 is the green hermetic mapping tests
  (`test_prompt_maps_http_request_action`,
  `test_prompt_maps_websocket_action`,
  `test_prompt_dismiss_returns_none`), not new runtime metrics.
- If a future task changes production `prompt()` mapping or presenter
  routing, observability belongs on that product change — not on this
  verification-debt item.
