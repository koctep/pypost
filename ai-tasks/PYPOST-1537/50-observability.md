# PYPOST-1537: Observability Implementation

## Logging Implementation

No logs were added. This task adds one automated check and does not change
production behavior. Selector text is not logged.

The open editor does not log. `FieldSelectorDelegate` in
`pypost/ui/delegates/field_selector_delegate.py` has no logger.
`createEditor` (lines 25-34), `setEditorData` (lines 36-46),
`_apply_live_feedback` (lines 60-72), and `setModelData` (lines 48-58) emit
no records while the person is still typing. `HiddenFieldsTable` and
`validate_field_selector` also have no logger on this path. None exist for
the live warning and the neutral-feedback half of the open edit.

The commit that ends the edit already logs. `setModelData` calls
`HiddenFieldsTableModel.setData`. Those existing DEBUG records do not include
selector text:

- `pypost/ui/models/hidden_fields_table_model.py` lines 176-183:
  `hidden_fields_table_model_set_data_cell` with `row`, `selector_len`, `ok`,
  and `is_empty`.
- `pypost/ui/models/hidden_fields_table_model.py` lines 190-196:
  `hidden_fields_table_model_trailing_row_expanded` with `edited_row`,
  `selector_len`, and `row_count`, when the committed cell is the trailing
  blank row and the stored text is non-empty.

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none
- **DEBUG**: none added. Existing commit records are listed above and do not
  include selector text.

### Log Structure

Log format used:

- Structured logs: yes for the existing model records (`event key=value`)
- Includes context: yes for those records (row, length, syntax flags, row
  count). Selector text is not included.
- Log levels: DEBUG only, and only on the existing commit path. No level was
  added for this task.

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

None of these were added or changed. The open-edit check is an automated
test, not a new telemetry source.

## Validation Results

Validation results:

- [x] Logs are correctly formatted — no new logs. Existing commit records stay
  `event key=value` and omit selector text.
- [x] Metrics are collected correctly — none were added; nothing new to collect
- [x] Logging works in error scenarios — no new error log. Advisory accept
  stays on the existing DEBUG commit records.
- [x] Large data structures are not logged — selector text is not written by
  the delegate or by the existing `setData` records
- [x] Metrics are available for monitoring — no new metrics

## Notes

The live open edit (warning on an unsupported selector, neutral feedback on a
supported selector) has no log. The finish that stores the draft is covered
only by the existing `setData` DEBUG records cited above, which record length
and flags rather than the selector string.
