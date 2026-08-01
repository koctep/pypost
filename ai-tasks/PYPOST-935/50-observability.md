# PYPOST-935: Observability Implementation

Identity-only additive change: no new production loggers, metrics, or
exception shapes. Dialog-settle **test diagnostics** gain an optional
`dialog_object_name` scalar in `_modal_diag()` (PYPOST-934 companion path).

## Logging Implementation

### Added Logs

None.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO / DEBUG**: none
  added in production or agent paths.
- Existing `ui_wait_settled` / `ui_wait_timeout` DEBUG events from the
  dialog-settle stack ([PYPOST-837](ui_wait),
  [PYPOST-919](agent_dialog_settle)) unchanged.

### Log Structure

Log format used:

- Structured logs: yes (existing agent DEBUG events)
- Includes context: yes (existing `condition`, `waited_ms`, `timeout_s`)
- Log levels: DEBUG/INFO on existing agent paths only

## Metrics Implementation (if applicable)

Not applicable — no runtime behavior change beyond stamping
`objectName` on `SettingsDialog`.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A

## Validation Results

Validation results:

- [x] Logs are correctly formatted — no new log events to validate
- [x] Metrics are collected correctly — N/A
- [x] Logging works in error scenarios — existing PYPOST-919/934 rewrap
  path unchanged; companion still asserts `step` + modal scalars
- [x] Large data structures are not logged — identity is a short string
- [x] Metrics are available for monitoring — N/A

## Notes

Test-only observability improvement: `_modal_diag()` now exposes
`dialog_object_name` alongside `dialog_title` and `active_modal_type`
for timeout companion asserts. Production observability posture
unchanged.
