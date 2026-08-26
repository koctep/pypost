# PYPOST-1161: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**:
  - `tabs_presenter._handle_save_websocket` — `ws_save_overwrite_failed reason=missing_snapshot ws_id=…` when overwrite returns no snapshot
- **WARNING**:
  - `websocket_save_orchestrator._save_new` — `ws_save_failed reason=missing_target_collection`
  - `websocket_save_orchestrator.save_as_profile` — `ws_save_as_flow_failed reason=missing_target_collection`
  - `collections_presenter.add_saved_websocket_to_tree` — `add_saved_websocket_to_tree_failed reason=collection_not_found collection_id=… ws_id=…`
- **NOTICE**: none
- **INFO**:
  - `websocket_tab._emit_save` — `ws_save_action_triggered source=<menu|shortcut>`
  - `websocket_tab._emit_save_as` — `ws_save_as_action_triggered source=<menu|shortcut>`
  - `websocket_save_orchestrator.save_as_profile` — `ws_save_as_flow_started`, `ws_save_as_flow_cancelled`, `ws_save_as_flow_completed source_ws_id=… new_ws_id=… target_collection_id=…`
  - `websocket_save_orchestrator._save_overwrite` — `ws_save_overwrite_cancelled`, `ws_save_stale_cancelled`, `ws_save_overwrite_succeeded ws_id=… collection_id=…`
  - `websocket_save_orchestrator._save_new` — `ws_save_new_succeeded ws_id=… name=… collection_id=…`
  - `collections_presenter.add_saved_websocket_to_tree` — `add_saved_websocket_to_tree_completed collection_id=… ws_id=…`
- **DEBUG**: none

### Log Structure

Log format used:

- Structured logs: yes — `event_name key=value` pairs per `doc/dev/logging.md`
- Includes context: yes — ws_id, collection_id, source, reason fields; no full connection payloads
- Log levels: INFO (happy path), WARNING (recoverable user cancel / missing collection), ERR (internal invariant)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: N/A — synchronous GUI save dialog flow
- **Throughput**: N/A
- **Error rate**: N/A — failures logged, not metered separately

### Business Metrics

Business metrics:

- `gui_save_actions_total{source=menu|shortcut|overwrite|new}` — `WebSocketTab` (menu/shortcut) and `WebSocketSaveOrchestrator` (overwrite/new)
- `gui_save_as_actions_total{source=menu|shortcut}` — `WebSocketTab` save-as entry points

Same counter families as HTTP (`doc/dev/request_actions.md`); no protocol label on save counters.

### System Health Metrics

System health metrics:

- **Resource usage**: N/A for this feature
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — save counters exposed via existing `MetricsManager` scrape path (no new counters)
- [ ] Grafana dashboards — unchanged
- [ ] Alerting rules — unchanged
- [ ] Log aggregation (ELK, Loki, etc.) — events grep-friendly by `ws_save_*` / `add_saved_websocket_*` prefixes

## Validation Results

Validation results:

- [x] Logs are correctly formatted — `%` formatting, snake_case event names
- [x] Metrics are collected correctly — orchestrator and tab entry points call `track_gui_save_action` / `track_gui_save_as_action`
- [x] Logging works in error scenarios — cancel, missing collection, missing snapshot paths covered
- [x] Large data structures are not logged — only ids, names, collection_id, source
- [x] Metrics are available for monitoring — existing GUI save counter registration

## Notes

Observability was implemented during Step 4; Step 6 documents the surface. No additional log lines were added in Step 6.
