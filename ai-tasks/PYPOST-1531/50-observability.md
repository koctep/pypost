# PYPOST-1531: Observability Implementation

## Logging Implementation

### Added Logs

None added. This task only adds regression coverage in
`tests/test_hidden_fields_event_paths.py`. NFR2 and the accepted architecture
keep production modules and interfaces unchanged. No new operation was
introduced, so new production logs would go beyond the task.

User-facing selector edits are signaled with Qt signals. The table widget does
not log. Verified paths:

- `pypost/ui/widgets/hidden_fields_table.py` has no logger. `keyPressEvent`
  sends Delete and Backspace to `remove_selected_rows` unless the view is
  editing. `contextMenuEvent` runs Add Selector via `add_row` or Remove
  Selected via `remove_selected_rows`.
- The same widget declares `data_changed` and `changed`, and forwards
  `HiddenFieldsTableModel.data_changed` and `changed`.
- `pypost/ui/widgets/request_editor.py` connects both table signals to
  `on_data_changed`, which updates request data and does not log the edit.
  Existing INFO lines there cover save, save-as, and copy-curl only.

The model already logs mutations at DEBUG. Logger:
`logging.getLogger(__name__)` in
`pypost/ui/models/hidden_fields_table_model.py`. Events are `event key=value`.
Selector text is omitted. Context is row index, counts, selector length, mode,
and syntax flags.

- **EMERG**: None added. Selector keyboard and menu edits have no
  system-failure path.
- **ALERT**: None added. These edits have no urgent paging condition.
- **CRIT**: None added. These edits have no critical process failure.
- **ERR**: None added. An empty selection returns from
  `HiddenFieldsTable.remove_selected_rows` when `selectedRows()` is empty and
  never calls the model, so there is no error log. A trailing-blank-only
  selection returns from `HiddenFieldsTableModel.remove_rows` with no log.
- **WARNING**: None added. Remove Selected without a selection is a disabled
  menu action, not a warning log.
- **NOTICE**: None added. This task adds no significant operational event.
- **INFO**: None added. Selector edits stay off INFO.
- **DEBUG**: None added. Existing model DEBUG lines already cover the calls
  these workflows make:
  - `add_row` logs `hidden_fields_table_model_add_row` with `mode`,
    `focus_row`, `has_text`, `ok`, and `row_count`. Menu Add Selector passes
    no text, so `mode` is `focus_trailing` and no row is inserted until the
    editor commits.
  - `setData` logs `hidden_fields_table_model_set_data_cell` with `row`,
    `selector_len`, `ok`, and `is_empty`. A non-empty trailing edit also logs
    `hidden_fields_table_model_trailing_row_expanded`.
  - `remove_rows` logs `hidden_fields_table_model_remove_rows` with
    `requested`, `removed`, and `row_count` after a real removal. Delete,
    Backspace, and Remove Selected all use this method.

### Log Structure

Log format used:

- Structured logs: no new logs. Existing model lines are `event key=value`.
- Includes context: no new context. Existing DEBUG context is row index,
  counts, selector length, mode, and syntax flags. Selector text is omitted.
- Log levels: none added. Existing selector mutation logs are DEBUG only.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: None added. Keyboard and menu coverage introduces no
  timed production operation.
- **Throughput**: None added. This is a desktop selector table, and this task
  adds no throughput counter.
- **Error rate**: None added. This task adds no failure path to count.

### Business Metrics

Business metrics:

- None added. Selector add and remove stay local UI edits. Persisted masking
  and save metrics on other paths are unchanged and out of scope.

### System Health Metrics

System health metrics:

- **Resource usage**: None added. No CPU, memory, or disk gauge. The widget
  and model are unchanged.
- **Component status**: None added. Status of a real selector edit is already
  a Qt signal, not a new health check. `HiddenFieldsTableModel` emits
  `data_changed` and `changed` from `setData`, inserting `add_row`,
  `remove_rows`, and `set_data`. A cell edit also emits Qt `dataChanged`.
  The view re-emits `data_changed` and `changed`. Add Selector on the blank
  row only logs DEBUG until the editor commits; that focus does not emit
  `data_changed` or `changed`.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

None of these were added. This task introduces no metric, dashboard, alert, or
log shipper. Existing DEBUG lines remain ordinary Python logging.

## Validation Results

Validation results:

- [ ] Logs are correctly formatted
- [ ] Metrics are collected correctly
- [ ] Logging works in error scenarios
- [ ] Large data structures are not logged
- [ ] Metrics are available for monitoring

Boxes stay unchecked because this step adds no logs or metrics to validate.
Source inspection confirms the DEBUG calls and Qt signal emits cited above are
unchanged. Step 4 already ran the event-path tests. This step does not rerun
them and does not modify production code or the test module.

## Notes

The observability decision is documentation only. `HiddenFieldsTable` and
`HiddenFieldsTableModel` stay as delivered. Diagnostics for selector add and
remove remain the existing model DEBUG events and the Qt `data_changed` and
`changed` signals consumed by `RequestEditor.on_data_changed`.
