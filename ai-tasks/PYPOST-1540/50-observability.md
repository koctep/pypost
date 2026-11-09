# PYPOST-1540: Observability Implementation

## Logging Implementation

N/A. No logs added.

`validate_field_selector` in `pypost/core/field_selector_syntax.py` is a
pure function. It has no logger today. This change only picks a warning
string inside that function. A log of the draft would record the selector
the person typed, including header names.

### Added Logs

No logs added:

- **EMERG**: N/A — none added
- **ALERT**: N/A — none added
- **CRIT**: N/A — none added
- **ERR**: N/A — none added
- **WARNING**: N/A — none added
- **NOTICE**: N/A — none added
- **INFO**: N/A — none added
- **DEBUG**: N/A — none added

### Log Structure

Log format used:

- Structured logs: no
- Includes context: no
- Log levels: none

## Metrics Implementation (if applicable)

N/A. No metrics added.

### Performance Metrics

Added performance metrics:

- **Response time**: N/A — none added
- **Throughput**: N/A — none added
- **Error rate**: N/A — none added

### Business Metrics

Business metrics:

- N/A: none added — `validate_field_selector` only chooses a warning string

### System Health Metrics

System health metrics:

- **Resource usage**: N/A — none added
- **Component status**: N/A — none added

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [ ] Logs are correctly formatted
- [ ] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [ ] Large data structures are not logged
- [ ] Metrics are available for monitoring

No production logging or metrics were added, so these checks do not apply.

## Notes

The user-facing signal stays the existing warning string. The hidden-fields
model and the live editor copy `message` into the tooltip. That string is
not a log line.

Logging the draft is intentionally omitted. The selector the person typed
can include header names. Recording it would put those names in a log.
