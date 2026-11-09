# PYPOST-1387: Observability Implementation

## Scope

Inline syntax validation for Hidden Field selectors (`validate_field_selector`,
model role surfacing, advisory `FieldSelectorDelegate`). Architecture Step 6
scoped this to **light observability: DEBUG counts only**, never selector
secret/path values beyond what is required for diagnosis. No new business or
Prometheus metrics; existing save/mask metrics (PYPOST-1377+) stay unchanged.

## Logging Implementation

### Added Logs

Module logger: `pypost.ui.models.hidden_fields_table_model` via
`logging.getLogger(__name__)`. Event names keep the PYPOST-1386
`hidden_fields_table_model_*` `event key=value` pattern.

Selector **string values are never logged** (counts, lengths, and boolean
`ok` / `is_empty` only) so sensitive field paths and header names do not enter
aggregation pipelines.

- **EMERG**: none — no system-failure path in syntax validation UI
- **ALERT**: none — no paging condition
- **CRIT**: none — no unrecoverable process failure
- **ERR**: none — validation is advisory; invalid selectors are stored and
  highlighted, not raised
- **WARNING**: none — no new warning site
- **NOTICE**: none — Python stdlib logging has no project NOTICE mapping
- **INFO**: none — syntax outcomes stay at DEBUG to avoid noise for typical
  small selector lists
- **DEBUG**:
  - `HiddenFieldsTableModel.set_data` (extended):
    `hidden_fields_table_model_set_data input_count=%d valid_count=%d row_count=%d ok_count=%d invalid_count=%d empty_count=%d`
    — bulk reset after filtering empty/whitespace; syntax tallies include the
    trailing blank row in `empty_count`
  - `HiddenFieldsTableModel.setData` (new, Edit/Display path):
    `hidden_fields_table_model_set_data_cell row=%d selector_len=%d ok=%s is_empty=%s`
    — one event per committed cell edit after `validate_field_selector`
  - `HiddenFieldsTableModel.setData` (unchanged from PYPOST-1386):
    `hidden_fields_table_model_trailing_row_expanded edited_row=%d selector_len=%d row_count=%d`
  - `HiddenFieldsTableModel.add_row` (extended with `ok=`):
    `hidden_fields_table_model_add_row mode=%s focus_row=%d has_text=%s ok=%s row_count=%d`
    — `ok` is `True` when `has_text` is false; otherwise mirrors cached syntax
  - `HiddenFieldsTableModel.remove_rows` (unchanged from PYPOST-1386):
    `hidden_fields_table_model_remove_rows requested=%d removed=%d row_count=%d`

Intentionally **not** logged:

- `pypost.core.field_selector_syntax.validate_field_selector` — called on every
  editor keystroke via the delegate; logging there would flood DEBUG
- `FieldSelectorDelegate._apply_live_feedback` / `setModelData` — live styling
  stays silent; commit observability is covered by model `setData`
- `HiddenFieldsTable` (view) — mutations already emit model events

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value`)
- Includes context: yes (counts, row index, selector length, ok/empty flags;
  no selector text)
- Log levels: DEBUG only for this change

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: none — `validate_field_selector` is a local pure check;
  NFR timing is covered by unit/repro tests, not OTel
- **Throughput**: N/A (desktop UI table, not a request pipeline)
- **Error rate**: N/A (advisory validation; no failure counter surface)

### Business Metrics

Business metrics:
- None added. Save/dirty and masking metrics from PYPOST-1377+ continue to
  cover persisted selector configuration and runtime masking:
  - `track_gui_save_action` (request save including hidden fields)
  - `track_hidden_value_mask_applied` / MCP field-masked counters (downstream)

### System Health Metrics

System health metrics:
- **Resource usage**: none added — cached `FieldSelectorSyntaxResult` on
  records avoids re-validation on paint; no new gauges
- **Component status**: Qt `dataChanged` / `data_changed` / `changed` signals
  remain the UI state channel for dirty tracking and role refresh

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A (no new counters/histograms)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A (local desktop configuration table)
- [x] Log aggregation (ELK, Loki, etc.) — DEBUG events are syslog-compatible
  `key=value` and safe to ship when DEBUG is enabled

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`event key=value`, mirrors PYPOST-1386 /
  `CollectionVariablesTableModel`)
- [x] Metrics are collected correctly — N/A (none added; documented)
- [x] Logging works in error scenarios — invalid selectors emit
  `ok=False` / raise `invalid_count` without exceptions
- [x] Large data structures are not logged — only integer counts / lengths /
  booleans; full selector lists and expression strings never written
- [x] Metrics available for monitoring — existing save/mask metrics unchanged

## Notes

- Architecture (`20-architecture.md`) explicitly scoped observability to light
  DEBUG counts and forbade logging selector secret values; this artifact
  matches that scope by extending the PYPOST-1386 model logger rather than
  introducing a second logger in core or the delegate.
- Enabling DEBUG for `pypost.ui.models.hidden_fields_table_model` is sufficient
  to diagnose bulk loads with invalid selectors and per-cell commit outcomes
  without app-wide DEBUG (and without keystroke noise from the live editor).
- No OTel / `MetricsTrackerProtocol` wiring was introduced: advisory syntax
  state is a presentation concern, not a new business event.
