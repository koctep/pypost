# PYPOST-448: Observability Implementation

## Logging Implementation

### Added / Modified Logs

Describe added logging:

- **EMERG**: N/A for this desktop scope.
- **ALERT**: N/A for this desktop scope.
- **CRIT**: N/A for this desktop scope.
- **ERR**: N/A added in this step.
- **WARNING**: N/A added in this step.
- **NOTICE**: N/A for this task.
- **INFO**:
  - `pypost/ui/dialogs/env_dialog.py` — existing `env_hidden_flag_changed` event now passes
    the key name through `HiddenToggleLogPolicy.format_key_name()` before emission.
  - Default (`log_hidden_key_names=False`): `key=********` (redacted via `HIDDEN_MASK`).
  - Opt-in (`log_hidden_key_names=True`): `key=<variable_name>` (PYPOST-437 behavior).
  - `env_name` and `hidden` fields are always logged; variable values are never logged.
- **DEBUG**: existing project-level debug logs retained; no new debug logs required.

### Log Structure

Log format used:

- Structured logs: yes (key=value fields in message template)
- Includes context: yes (`env_name`, `key`, `hidden`)
- Log levels: INFO (modified path only); existing DEBUG/INFO/WARNING/ERROR unchanged

### Policy Module

- `pypost/core/hidden_toggle_log_policy.py` — centralizes key-name representation for the
  toggle log event; ensures redaction logic is not duplicated at call sites.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: not added for this ticket.
- **Throughput**: not added for this ticket.
- **Error rate**: not added for this ticket.

### Business Metrics

Business metrics:

- not applicable. Toggle logging is a low-frequency UI observability event; a counter would
  add noise without operational value for this desktop scope.

### System Health Metrics

System health metrics:

- no new metrics; existing app metrics subsystem remains unchanged.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted
- [ ] Metrics are collected correctly (N/A — no new metrics)
- [x] Logging works in error scenarios (toggle path unchanged; policy applied on success path)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring (N/A)

Validation commands:

- `test_hidden_toggle_logs_masked_key_by_default` in `tests/test_env_dialog.py`
- `test_hidden_toggle_logs_readable_key_when_enabled` in `tests/test_env_dialog.py`
- `tests/test_hidden_toggle_log_policy.py` — policy unit tests

## Notes

- Security posture: default mode redacts variable key names in toggle logs; values were
  never logged (PYPOST-437 constraint preserved).
- Behavioral change: out-of-box logging is stricter than PYPOST-437; users enable full
  key-name visibility via Settings checkbox.
- Setting changes apply to subsequent `EnvironmentDialog` sessions (constructor snapshot).
