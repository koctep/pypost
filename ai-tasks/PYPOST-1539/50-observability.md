# PYPOST-1539: Observability Implementation

## Logging Implementation

No logs were added. No metrics were added. The double-dot reject is a pure
return inside `validate_field_selector`. Selector text stays out of logs.

`validate_field_selector` in `pypost/core/field_selector_syntax.py` has no
logger. The new reject is lines 113-115: when the stripped path contains
`..`, it returns `_invalid(_UNSUPPORTED_MESSAGE)`. That return does not
log. None.

The late `..` check in `_validate_path` (lines 75-76) also returns
`_invalid` and does not log. None.

Call sites of `validate_field_selector`:

- `FieldSelectorDelegate._apply_live_feedback` in
  `pypost/ui/delegates/field_selector_delegate.py` calls it at line 62.
  That module has no logger. None.
- `HiddenFieldsTableModel` in
  `pypost/ui/models/hidden_fields_table_model.py` calls it from
  `_syntax_for` at line 41. Existing DEBUG records in that file
  (lines 176-183, 190-196, 219-229, 243-251, 266-274, and 317-323) log
  row indexes, lengths, boolean flags, and counts. They omit selector
  text. They do not record that the double-dot reject fired.

No existing log covers the double-dot reject path.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none
- **DEBUG**: none added. The existing table-model records cited above
  omit selector text and do not name the double-dot reject.

### Log Structure

Log format used:

- Structured logs: yes for the existing table-model records
  (`event key=value`)
- Includes context: yes for those records (indexes, lengths, flags, and
  counts only). Selector text is omitted.
- Log levels: DEBUG only, and only on the existing table-model records.
  No level was added for this task. `validate_field_selector` and the
  live editor do not log.

## Metrics Implementation (if applicable)

No metrics were added.

### Performance Metrics

Added performance metrics:

- **Response time**: none
- **Throughput**: none
- **Error rate**: none

### Business Metrics

Business metrics:

- None added.

### System Health Metrics

System health metrics:

- **Resource usage**: none
- **Component status**: none

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

None of these were added or changed. A broken double-dot draft stays a
failed syntax verdict and a failed test
(`tests/test_pypost_1539_failing_repro.py`), not a new telemetry source.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — no new logs. The existing
  table-model records stay `event key=value` and omit selector text.
- [x] Metrics are collected correctly — none were added; nothing new to
  collect
- [x] Logging works in error scenarios — no new error log. The
  double-dot reject path has no error record.
  `validate_field_selector` stays silent.
- [x] Large data structures are not logged — selector text is omitted by
  `validate_field_selector` and by the table-model records
- [x] Metrics are available for monitoring — no new metrics

## Notes

This step adds no log line and no metric. The reject at
`field_selector_syntax.py` lines 113-115 does not log. Production code
and tests were left unchanged.
