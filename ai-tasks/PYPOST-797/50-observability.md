# PYPOST-797: Observability Implementation

## Logging Implementation

### Added Logs

No new log statements were required. The Step 3 fix completes the mouse path into existing
new-tab observability:

- **INFO**: `pypost/ui/presenters/tabs_presenter.py` — `handle_new_tab` logs
  `new_tab_action_triggered source=<source> tabs_before=<count>` when the **+** button
  `clicked` signal reaches `TabsPresenter` via `new_tab_requested` (source=`plus_button`).
- **INFO**: `pypost/ui/presenters/collection_tree_actions.py` — unchanged
  `collection_request_open_new_tab` for collections context menu (regression path only).

### No new logs in `RequestTabHeader` (`tab_header.py`)

Rationale:

- The header emits `new_tab_requested`; `TabsPresenter.handle_new_tab` is the single
  aggregation point for all new-tab sources (shortcut, plus button, collections).
- Logging at the widget layer would duplicate the presenter INFO event with no extra
  diagnostic value — same pattern as PYPOST-293.
- `_on_tab_bar_clicked` (plus-tab chrome fallback) routes to the same presenter handler;
  one log per user action is sufficient.

### Log Structure

Log format used:
- Structured logs: yes (key=value event names and scalar fields)
- Includes context: yes (`source`, `tabs_before` — request tabs only, excludes plus placeholder)
- Log levels: INFO unchanged for new-tab actions

## Metrics Implementation

### Business Metrics

Unchanged — existing counter covers the restored **+** click path:

- **New tab actions**: `gui_new_tab_actions_total{source="plus_button"}` —
  `MetricsRegistry.track_gui_new_tab_action` / OTEL equivalent in
  `TabsPresenter.handle_new_tab()` (`pypost/ui/presenters/tabs_presenter.py:308-312`).
- Other sources remain: `shortcut`, `collections_context`, `unknown`.

### Performance Metrics

None. Tab creation is a synchronous GUI operation; no latency or throughput instrumentation
added for this one-line signal wiring fix.

### System Health Metrics

None. No new health probes; `MetricsManager` stack unchanged.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (existing `gui_new_tab_actions_total` — no schema change)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

No new dashboards or alert rules — this task restores an existing user action to the
established metrics and logging pipeline.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (key=value convention; presenter path exercised by
  `test_plus_tab_click_adds_request_tab`)
- [x] Metrics are collected correctly (`plus_button` source normalized in
  `metrics_registry._normalize_new_tab_source`)
- [x] Logging works in the fixed click scenario (+ button `QTest.mouseClick` →
  `handle_new_tab("plus_button")` → INFO + counter)
- [x] Large data structures are not logged (only scalar `source` and `tabs_before`)
- [x] Metrics are available for monitoring (unchanged baseline; `test_track_gui_new_tab_action_known_sources`)

## Notes

- The only production change in Steps 3–4 was `plus_btn.clicked.connect(...)` in
  `ensure_plus_tab()`. Observability required no additional code — the defect was a missing
  signal wire, not absent instrumentation.
- After the fix, support can confirm **+** clicks via log grep
  `new_tab_action_triggered source=plus_button` or Prometheus
  `gui_new_tab_actions_total{source="plus_button"}`.
- Keyboard shortcut (`source=shortcut`) and collections context menu
  (`source=collections_context`) paths were already observable; this step confirms they
  remain unchanged.

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: 900
