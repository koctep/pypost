# PYPOST-1159: Observability Implementation

Last-tab empty-workspace replacement routes through the existing blank-tab
entry (`close_workspace_tab` → `handle_new_tab("last_tab")`). No new log
events or Prometheus instruments were required — Step 4 wired the fallback
into the path that already emits structured INFO logs and
`gui_new_tab_actions_total`. This step documents that reuse and validates
it against Step 3/4 tests.

## Logging Implementation

### Added Logs

No new log statements. `tabs_presenter_close.close_workspace_tab` delegates
to `handle_new_tab("last_tab")` when `_request_tab_count() == 0`; all
picker-path logging lives in `tabs_presenter` (shipped PYPOST-1157).

Fields are `source`, `tabs_before`, and `protocol` only — no URLs,
headers, bodies, or tab widgets (FR-6.3 / FR-6.4).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE; picker events use INFO)
- **INFO** (reused via `handle_new_tab("last_tab")`):
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_triggered source=last_tab tabs_before=0` — picker shown
    after the last workspace tab is removed
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_cancelled source=last_tab` — user dismissed the picker;
    empty workspace allowed; no metric
  - `pypost.ui.presenters.tabs_presenter.open_blank_tab`:
    `new_tab_action_completed source=last_tab protocol=%s` — HTTP
    (`http`), WebSocket (`websocket`), or MCP Client (`mcp_client`) confirm
- **DEBUG**: none

`close_workspace_tab` intentionally emits no logs — close policy and
blank-tab observability stay in one place (`handle_new_tab`).

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`source`, `tabs_before`, `protocol`)
- Log levels: INFO

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Picker and blank-tab routing are synchronous GUI work; no
latency histogram is required for last-tab close.

### Business Metrics

Reused from Step 4 (registered `last_tab` in `_NEW_TAB_ACTION_SOURCES`;
no new counter):

- **gui_new_tab_actions_total{source="last_tab", protocol}**: completed
  blank-tab choice after last-tab close. `protocol`: `http`, `websocket`,
  `mcp_client`. Incremented in `TabsPresenter.open_blank_tab` via
  `track_gui_new_tab_action(source, protocol=protocol.value)`.
  Picker cancel does **not** increment (same rule as `Ctrl+N` / **+**).

Operator inventory: `doc/prometheus_monitoring.md` GUI table lists
`last_tab` on the `source` label for `gui_new_tab_actions_total`.

Normalization (`metrics_registry._normalize_new_tab_source`,
`metrics_otel` equivalent): unknown source strings map to `unknown`;
`last_tab` is preserved.

### System Health Metrics

None added. Last-tab close does not change resource gauges.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`gui_new_tab_actions_total` with `source=last_tab`
      documented in `doc/prometheus_monitoring.md`)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`) — same
      `handle_new_tab` / `open_blank_tab` events; `source=last_tab` flows
      through unchanged (`test_handle_new_tab_cancel_logs_source_without_metric`,
      `test_handle_new_tab_confirm_logs_source_and_protocol` cover the
      logging contract for other sources; last-tab uses identical code)
- [x] Metrics are collected correctly —
      `test_close_last_tab_http_confirm_opens_request_tab` asserts
      `track_gui_new_tab_action("last_tab", protocol="http")`;
      `test_track_gui_new_tab_action_last_tab_source` scrapes
      `gui_new_tab_actions_total{source="last_tab",protocol="http"}`
- [x] Logging works in cancel scenario —
      `test_close_last_tab_cancel_creates_no_replacement` asserts
      `_request_tab_count() == 0` and metric not called (cancel path in
      `handle_new_tab` logs `new_tab_action_cancelled` before return)
- [x] Large data structures are not logged — no URL/header/body fields in
      new-tab events (existing FR-6.3 guard)
- [x] Metrics are available for monitoring (`/metrics` scrape via
      `MetricsRegistry` / OTel backend)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`; that is the acceptance-gate owner's action after review.
- No production code changes in this step; gaps were closed in Step 4 by
  routing empty strip through `handle_new_tab("last_tab")` and registering
  the metrics source.
- Distinct `last_tab` source separates last-close picker usage from
  `plus_button`, `shortcut`, and `collections_context` for operator
  attribution (FR-6.1).
