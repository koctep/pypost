# PYPOST-1157: Observability Implementation

## Logging Implementation

### Added Logs

Picker-path analysis: `handle_new_tab` already logged INFO
`new_tab_action_triggered source=%s tabs_before=%d` before the protocol
menu. After that, cancel and confirm were silent. Metrics already record
completed choices (`source` + `protocol`) and skip cancel. Step 6 adds
structured INFO logs for those two outcomes. Fields are `source` and
`protocol` only — no URLs, headers, bodies, or tab widgets (FR-6.3; none
exist yet).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE; picker events use INFO,
  matching existing presenter logs)
- **INFO**:
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab` (reused):
    `new_tab_action_triggered source=%s tabs_before=%d` — picker shown for
    `shortcut` (`Ctrl+N`) or `plus_button` (tab-bar +)
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab` (added):
    `new_tab_action_cancelled source=%s` — user dismissed the picker; no
    metric
  - `pypost.ui.presenters.tabs_presenter.open_blank_tab` (added):
    `new_tab_action_completed source=%s protocol=%s` — HTTP or WebSocket
    confirm; `protocol` is `http` or `websocket`
- **DEBUG**: none

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`source`, `tabs_before`, `protocol`)
- Log levels: INFO

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Picker and blank-tab routing are synchronous GUI work; no
latency histogram is required.

### Business Metrics

Reused from Step 4 (not newly registered here):

- **gui_new_tab_actions_total{source, protocol}**: completed blank-tab
  choice. Labels: `source` (`plus_button`, `shortcut`,
  `collections_context`, `unknown`); `protocol` (`http`, `websocket`,
  `unknown`). Incremented in `TabsPresenter.open_blank_tab` via
  `track_gui_new_tab_action(source, protocol=protocol.value)`. Cancel does
  not increment. Collections **New tab** still defaults `protocol=unknown`.

Operator inventory: `doc/prometheus_monitoring.md` GUI table now lists
both labels (was `source` only). `doc/dev/` updates belong to Step 8.

### System Health Metrics

None added. Blank-tab creation does not change resource gauges.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`gui_new_tab_actions_total` labels documented)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`)
- [x] Metrics are collected correctly (Step 4 tests reused; cancel still
      asserts the metric is not called)
- [x] Logging works on cancel and HTTP/WS confirm (new presenter tests)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (`/metrics` scrape)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`; that is the acceptance-gate owner's action after review.
- `tabs_presenter.py` is 746 LOC (cap 785). Snapshot
  `ai-tasks/PYPOST-376/baseline-metrics.md` regenerated for that LOC.
- No new Prometheus instrument; the `protocol` label was added in Step 4.
