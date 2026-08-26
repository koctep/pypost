# PYPOST-1160: Observability Implementation

WS-TM-4: Collections WebSocket context-menu parity. Logging and metrics reuse
the existing collections menu and GUI presenter families; this step adds
WebSocket-specific **New tab** telemetry and delete-close diagnostics.

## Logging Implementation

### Added Logs

Fields are ids, names, counts, and `item_type` only — no URL, headers,
subprotocols, or full `WebSocketConnection` dumps.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**:
  - `pypost.ui.presenters.collection_tree_actions.handle_rename_committed`:
    `collection_rename_failed` — rename persistence exception
  - `pypost.ui.presenters.collection_tree_actions.handle_delete`:
    `collection_delete_failed` — delete persistence exception
- **WARNING**:
  - `pypost.ui.presenters.collection_tree_actions.handle_rename_committed`:
    `collection_rename_not_found` / `collection_rename_rejected_empty`
  - `pypost.ui.presenters.collection_tree_actions.handle_delete`:
    `collection_delete_not_found`
  - `pypost.ui.presenters.collection_tree_actions._sync_rename_tree_item`:
    `collection_rename_tree_sync_failed` — websocket row missing after rename
- **NOTICE**: none (Python logging has no NOTICE; lifecycle uses INFO)
- **INFO** (added or extended this story):
  - `pypost.ui.presenters.collection_tree_actions.show_context_menu`:
    `collection_websocket_open_new_tab ws_id=%s ws_name=%s` — **New tab** on
    a WebSocket profile row
  - `pypost.ui.presenters.tabs_presenter_ws_close.close_tabs_for_websocket_ids`:
    `close_tabs_for_deleted_websockets closed_count=%d ws_ids=%s` — tabs
    removed after profile/collection delete (user confirmed or silent close)
- **INFO** (existing, reused for websocket rows once menu resolves):
  - `collection_request_open_new_tab` — HTTP **New tab** (parallel path)
  - `collection_export_selected item_type=%s item_id=%s` — export from WS row
  - `collection_rename_committed` / `collection_delete_committed` —
    rename/delete success with `item_type=websocket`
  - `collection_rename_selected` / `collection_delete_selected` /
    `collection_delete_cancelled` — menu dispatch
- **DEBUG**: none for WS collections menu

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`ws_id`, `ws_name`, `item_type`, `closed_count`,
  `ws_ids`)
- Log levels: INFO, WARNING, ERROR
- Payload fields: none (no connection object or handshake dumps)

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Menu actions and tab close are synchronous GUI work.

### Business Metrics

Extended existing GUI counters (no new Prometheus series names):

- **Collections New tab**: `gui_new_tab_actions_total{source="collections_context", protocol="websocket"}` — recorded when user chooses **New tab** on a WebSocket profile row (`CollectionTreeActions.show_context_menu`). HTTP rows continue with default `protocol=unknown` until a follow-up aligns HTTP labeling.
- **Rename**: `gui_collection_rename_actions_total{item_type="websocket", status=…}` — `selected`, `cancelled`, `rejected_empty`, `not_found`, `error`, `succeeded` (existing counter; websocket rows now reach dispatch).
- **Delete**: `gui_collection_delete_actions_total{item_type="websocket", status=…}` — same status labels as rename.

### System Health Metrics

None added.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics — via existing `MetricsRegistry` / `gui_new_tab_actions_total` and collection rename/delete counters
- [ ] Grafana dashboards — no WS-specific dashboard change
- [ ] Alerting rules — none
- [ ] Log aggregation (ELK, Loki, etc.) — standard app logging only

## Validation Results

Validation results:

- [x] Logs are correctly formatted — snake_case events with scalar fields
- [x] Metrics are collected correctly — `test_websocket_new_tab_emits_isolated_open_with_protocol_metric` asserts `protocol="websocket"`
- [x] Logging works in error scenarios — rename/delete failure paths use WARNING/ERROR
- [x] Large data structures are not logged — ids and names only
- [x] Metrics are available for monitoring — existing Prometheus export

## Notes

Delete-profile tab prompt button choices (**Close tab** / **Keep the tab**)
are not logged individually; only the aggregate `close_tabs_for_deleted_websockets`
INFO line records how many tabs were closed. User cancel on the prompt leaves
the tab open with no log line (same pattern as HTTP silent sibling reload).
