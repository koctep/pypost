# PYPOST-1158: Observability Implementation

WS-TM-2: blank WebSocket draft tab lifecycle. Logging covers session
persist (FR-5) and dirty-close (FR-8). Connect, stream, and session-slot
metrics stay with existing WebSocket presenter / WS-10 paths.

## Logging Implementation

### Added Logs

Picker and blank-tab creation already log INFO in `tabs_presenter`
(`new_tab_action_triggered` / `_cancelled` / `_completed`). This step
adds draft persist and close events in `tabs_presenter_draft` so
`tabs_presenter.py` stays at the 785 LOC cap.

Fields are `connection_id`, `choice`, and counts only — no URL, headers,
subprotocols, or `WebSocketConnection` dumps.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE; lifecycle uses INFO)
- **INFO** (added this story):
  - `pypost.ui.presenters.tabs_presenter_draft.collect_persistable_open_tab_ids`:
    `websocket_draft_omitted_from_open_tabs connection_id=%s` — unsaved
    WS draft id not written to `open_tabs`
  - `pypost.ui.presenters.tabs_presenter_draft.collect_persistable_open_tab_ids`:
    `websocket_saved_tab_persisted_in_open_tabs connection_id=%s` —
    collection-backed WS id appended to `open_tabs`
  - `pypost.ui.presenters.tabs_presenter_draft.collect_persistable_open_tab_ids`:
    `websocket_open_tabs_filter omitted_draft_count=%d persisted_ws_count=%d`
    — per-`save_tabs_state` WS filter totals (emitted when either count
    is non-zero)
  - `pypost.ui.presenters.tabs_presenter_draft.confirm_close_websocket_draft`:
    `websocket_draft_dirty_close_prompt connection_id=%s choice=%s` —
    Discard/Keep prompt; `choice` is `discard` or `keep`
  - `pypost.ui.presenters.tabs_presenter_draft.confirm_close_websocket_draft`:
    `websocket_draft_clean_close connection_id=%s` — unsaved draft closed
    with no prompt (factory-clean)
- **INFO** (existing, reused — not added here):
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_triggered source=%s tabs_before=%d`
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_cancelled source=%s`
  - `pypost.ui.presenters.tabs_presenter.open_blank_tab`:
    `new_tab_action_completed source=%s protocol=%s`
  - `pypost.ui.presenters.tabs_presenter.restore_tabs`:
    `restore_tabs_item_not_found item_id=%s` (WARNING) — leftover id not
    in registry; drafts must not produce this after the omit gate
- **DEBUG**: none for draft persist / close

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`connection_id`, `choice`, `omitted_draft_count`,
  `persisted_ws_count`)
- Log levels: INFO
- Payload fields: none (no URL, headers, body, or connection object dumps)

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Registry-gated persist and the Discard/Keep prompt are
synchronous GUI work; no latency histogram is required.

### Business Metrics

None added this story. Draft omit and dirty-close are diagnostic log
events, not Prometheus series.

The project already has GUI presenter metrics from earlier stories
(`gui_new_tab_actions_total{source, protocol}` in
`TabsPresenter.open_blank_tab`). That counter records blank-tab
**creation** (WS-TM-1 / PYPOST-1157), not session omit or close. No new
instrument was registered for persist/omit/close.

Existing WebSocket session counters (`websocket_sessions_opened_total`,
`websocket_sessions_closed_total`) remain owned by connect/teardown, not
this draft-lifecycle path.

### System Health Metrics

None added. Draft persist and close do not change resource gauges or
session-slot counts.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics (N/A for this story — no new instruments;
      existing GUI new-tab and WS session counters were not extended)
- [ ] Grafana dashboards (not invented this story)
- [ ] Alerting rules (omit and Keep/Discard are expected user flows)
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`); persist/close
      include `connection_id` (and `choice` / counts) only
- [x] Metrics are collected correctly: N/A — no new counters; existing
      `protocol=websocket` new-tab tests remain the source of truth for
      creation metrics
- [x] Logging works in persist and close scenarios:
      `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_omitted_websocket_draft_id`
      `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_persisted_saved_websocket_id`
      `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_close_dirty_websocket_draft_logs_keep_and_discard`
      `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_close_clean_websocket_draft_logs_without_prompt`
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring: N/A for this story (no new
      series; `/metrics` scrape of existing GUI/WS counters is unchanged)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`; that is the acceptance-gate owner's action after review.
- Logs live in `tabs_presenter_draft.py` so `tabs_presenter.py` remains
  785 / 785 LOC.
- Python has no syslog NOTICE; INFO matches existing presenter events.
- No Prometheus stack was invented for UI presenter persist/close.
  Draft omit is the expected FR-5 path, not a failure signal.
