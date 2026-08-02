# PYPOST-976: Observability Implementation

## Scope

Test-only coverage task — no production logging or metrics changes. Opt-in fill
on the request body editor (`CodeEditor` / `QPlainTextEdit`) already emits DEBUG
`ui_action_applied` with `via_key_clicks=true` (`pypost/agent/ui_actions.py`,
PYPOST-917); Step 4 added a session behavioral smoke only.

## Logging Implementation

### Added Logs

No new log statements — test-only task.

Existing production observability for the path under test:

- **DEBUG** `ui_action_applied` on successful `ui_fill` with scalar
  `via_key_clicks=true` (lowercase); fill **text is never logged**
  (PYPOST-851 / NFR3).
- Logger: `pypost.agent.ui_actions`.
- Widget id in log: `pypost_request_body_edit` (`REQUEST_BODY_EDIT`).

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

- [x] No new logs required — existing DEBUG contract unchanged
- [x] Metrics N/A
- [x] CI failure output remains actionable — behavioral assert on
  `toPlainText()` after session keyClicks fill
- [x] Large data structures are not logged — fill text not part of test scope
- [x] N/A for production observability documented

## Notes

- New test `test_ui_fill_via_key_clicks_session_request_body` asserts widget
  content only; caplog proof for body-editor keyClicks fill is deferred to
  [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977) (explicitly out
  of scope for this task).
- Sibling session smoke `test_ui_fill_via_key_clicks_session` (URL field) uses
  the same behavioral-only pattern; line-edit caplog remains on
  `test_ui_action_applied_caplog` (PYPOST-944).
- Parent coverage task
  [PYPOST-945/50-observability.md](../PYPOST-945/50-observability.md) documents
  the same existing DEBUG contract for fixture plain/rich proofs.

## Self-Review (50-observability.mdc)

- [x] Key path covered by existing structured DEBUG event
- [x] No large payloads / fill text in logs
- [x] Documented in this file
