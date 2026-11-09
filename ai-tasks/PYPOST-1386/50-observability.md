# PYPOST-1386: Observability Implementation

## Scope

UI virtualization refactor of `HiddenFieldsTable` to `QAbstractTableModel` +
`QTableView`. Architecture Step 6 called for structured debug/trace logging on
bulk model updates and trailing-row expansions. No new business or Prometheus
metrics are required for this presentation-layer change; existing downstream
masking/save metrics (PYPOST-1377/1378/1379) remain unchanged.

## Logging Implementation

### Added Logs

Module logger: `pypost.ui.models.hidden_fields_table_model` via
`logging.getLogger(__name__)`. Event names follow the
`collection_variables_table_model_*` `event key=value` pattern. Selector string
values are never logged (counts and lengths only) to avoid leaking sensitive
field paths into aggregation pipelines.

- **EMERG**: none — no system-failure path in this UI model
- **ALERT**: none — no paging condition
- **CRIT**: none — no unrecoverable process failure
- **ERR**: none — model operations are bounded and return bool / no-op on
  invalid input; no new error path
- **WARNING**: none — no new warning site (invalid indices are silent no-ops)
- **NOTICE**: none — Python stdlib logging has no project NOTICE mapping
- **INFO**: none — bulk edits stay at DEBUG to avoid noise for typical small
  selector lists
- **DEBUG**:
  - `HiddenFieldsTableModel.set_data`:
    `hidden_fields_table_model_set_data input_count=%d valid_count=%d row_count=%d`
    — bulk reset after filtering empty/whitespace selectors; `row_count`
    includes the trailing blank row
  - `HiddenFieldsTableModel.setData` (trailing expand path):
    `hidden_fields_table_model_trailing_row_expanded edited_row=%d selector_len=%d row_count=%d`
    — auto-append of a new blank trailing row after a non-empty trailing edit
  - `HiddenFieldsTableModel.add_row`:
    `hidden_fields_table_model_add_row mode=%s focus_row=%d has_text=%s row_count=%d`
    — `mode` is `reuse_trailing`, `focus_trailing`, or `insert`
  - `HiddenFieldsTableModel.remove_rows`:
    `hidden_fields_table_model_remove_rows requested=%d removed=%d row_count=%d`
    — batch delete of non-trailing rows; trailing blank invariant preserved

`HiddenFieldsTable` (view) adds no extra logs: it delegates mutations to the
model, so model events already cover bulk load, expand, add, and remove.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value`)
- Includes context: yes (counts, row indices, mode flags; no selector text)
- Log levels: DEBUG only for this change

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: none added — `set_data` for 1,000+ rows remains a local
  synchronous reset; NFR timing is covered by unit/repro tests, not OTel
- **Throughput**: N/A (desktop UI table, not a request pipeline)
- **Error rate**: N/A (no new failure metric surface)

### Business Metrics

Business metrics:
- None added. Save/dirty and masking metrics from PYPOST-1377+ continue to
  cover persisted selector configuration and runtime masking:
  - `track_gui_save_action` (request save including hidden fields)
  - `track_hidden_value_mask_applied` / MCP field-masked counters (downstream)

### System Health Metrics

System health metrics:
- **Resource usage**: none added — virtualization itself is the memory/FPS
  improvement; no new gauges for viewport row count
- **Component status**: Qt object tree + existing `data_changed` / `changed`
  signals remain the UI state observability channel for dirty tracking

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A for this refactor (no new counters/histograms)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A (local desktop configuration table)
- [x] Log aggregation (ELK, Loki, etc.) — DEBUG events are syslog-compatible
  `key=value` and safe to ship when DEBUG is enabled

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`event key=value`, mirrors
  `CollectionVariablesTableModel`)
- [x] Metrics are collected correctly — N/A (none added; documented)
- [x] Logging works in error scenarios — invalid indices remain silent no-ops;
  successful mutations emit DEBUG with counts
- [x] Large data structures are not logged — only integer counts / lengths /
  modes; full selector lists never written
- [x] Metrics available for monitoring — existing save/mask metrics unchanged

## Notes

- Architecture (`20-architecture.md` Step 6) explicitly scoped observability to
  structured debug/trace for bulk updates and trailing-row expansion; this
  artifact matches that scope plus add/remove for complete mutation coverage.
- Enabling DEBUG for `pypost.ui.models.hidden_fields_table_model` is sufficient
  to diagnose large-list load and auto-expand behavior without turning on
  app-wide DEBUG.
- No OTel / `MetricsTrackerProtocol` wiring was introduced into the model or
  view: injecting metrics into a pure Qt table model would couple UI data to
  the metrics registry without a new business event to track.
