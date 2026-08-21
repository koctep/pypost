# PYPOST-1064: Observability Implementation

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | `CollectionsPresenter` (export routing), `CollectionTreeActions` (context-menu selection), `CollectionExportActions` (target resolution & export execution) |
| Critical paths | Context-menu export (`source_index` explicit) vs. sidebar toolbar button export (`source_index=None` fallback to `currentIndex()`) → target resolution → file save → completed/failed outcome |
| Performance metrics | Not required — rare interactive desktop user-initiated action |

When exporting a collection, target resolution adheres to the explicit `source_index` parameter when supplied (e.g., from context-menu click on a collection or request item), overriding any distant `currentIndex()`. Observability relies on structured event logging across selection and execution phases.

## Logging Implementation

### Added / Adhered Logs

- **EMERG**: N/A - no system-level emergencies applicable to local export
- **ALERT**: N/A - no immediate human intervention required
- **CRIT**: N/A - no critical application-crashing errors
- **ERR**: N/A - export failures are handled gracefully as warnings
- **WARNING**:
  - `pypost.ui.presenters.collection_export_actions` - `collection_export_no_selection` (no exportable collection found for the resolved index)
  - `pypost.ui.presenters.collection_export_actions` - `collection_export_failed reason=%s` (serialization or file write failure)
- **NOTICE**: N/A
- **INFO**:
  - `pypost.ui.presenters.collection_tree_actions` - `collection_export_selected item_type=%s item_id=%s` (emitted on context-menu item selection before delegating to export actions)
  - `pypost.ui.presenters.collection_export_actions` - `collection_export_completed collection_name=%s request_count=%d path=%s` (successful single collection export)
  - `pypost.ui.presenters.collection_export_actions` - `collections_export_completed collection_count=%d request_count=%d path=%s` (successful all-collections backup export)
  - `pypost.ui.presenters.collection_export_actions` - `collections_export_cancelled` (user cancelled all-collections export prompt)
- **DEBUG**: N/A

### Log Structure

Log format used:
- Structured logs: yes (`<event_name> <key1>=<value1> <key2>=<value2>`)
- Includes context: yes (`item_type`, `item_id`, `collection_name`, `request_count`, `path`, `reason`)
- Log levels: INFO, WARNING
- Safe masking & data hygiene: Large payloads (serialized collection JSON, request bodies, auth headers) are not logged; only metadata (counts, names, destination paths) are output.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A

Export is an interactive user action; timing and volume metrics are not applicable.

### Business Metrics

- N/A — GUI metrics track create/delete/rename operations; export routing is covered via structured logs.

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A (no new time series needed)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A (standard desktop application log output)

## Validation Results

Validation results:
- [x] Logs are correctly formatted according to key=value conventions
- [x] Metrics are collected correctly — N/A (none needed)
- [x] Logging works in error scenarios (`collection_export_no_selection`, `collection_export_failed`)
- [x] Large data structures are not logged (payload bodies and secret headers excluded)
- [x] Metrics are available for monitoring — N/A

## Notes

- Target routing verification ensures that passing `source_index` to `CollectionsPresenter.export_collection` or invoking `_export_collection_at_index` correctly targets the selected collection/parent without altering or getting confused by tree `currentIndex()`.
- Preceding `collection_export_selected` (when triggered via context menu) and subsequent `collection_export_completed` / `collection_export_failed` events provide full end-to-end traceability for export operations.
