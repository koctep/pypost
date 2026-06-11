# PYPOST-293: Observability Implementation

## Logging Implementation

### Added Logs

No new log statements were required. Existing new-tab logging remains:

- **INFO**: `TabsPresenter.handle_new_tab` — `new_tab_action_triggered source=<source> tabs_before=<count>`
  (count now excludes the plus placeholder tab via `_request_tab_count()`).

### Log Structure

Log format used:
- Structured logs: yes (key=value pairs)
- Includes context: source, tabs_before
- Log levels: INFO unchanged

## Metrics Implementation

### Business Metrics

Unchanged:
- `gui_new_tab_actions_total{source=plus_button|shortcut|unknown}` — still incremented in
  `handle_new_tab()`.

## Monitoring Integration

No changes to Prometheus wiring or metrics registration.

## Validation Results

Validation results:
- [x] Logs remain correctly formatted
- [x] Metrics path unchanged (`track_gui_new_tab_action`)
- [x] `tabs_before` metric context reflects request tabs only (not plus placeholder)
- [x] No large data structures logged

## Notes

Removing `_position_add_tab_button()` eliminates per-resize reposition work; no new performance
metrics were added for this minor win.
