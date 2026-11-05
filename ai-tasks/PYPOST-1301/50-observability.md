# PYPOST-1301: Observability Implementation

## Logging Implementation

### Scope and Gap Analysis

Critical paths for this task:

1. **Tab close while export busy** — defer page disposal until `export_finished`
2. **Tab close while idle** — immediate `deleteLater` (no timeout noise)
3. **App exit while export busy** — abandon ownership after remaining budget
4. **App exit while idle** — dispose without abandon

Architecture requires structured finish-wait timeout naming with distinct
`action=` values (`dispose_deferred`, `export_abandoned`), plus a completed
event for deferred dispose. No transcript payloads/paths beyond existing
export-start conventions.

### Added Logs

- **WARNING**: `tabs_presenter_ws_export_teardown.dispose_websocket_tab_page`
  (`mode=tab_close`, still deferred after schedule) —
  `websocket_stream_export_worker_finish_wait_timeout wait_ms=<int>
  action=dispose_deferred`. Emitted only when the page remains in the deferred
  set after the post-connect busy re-check.
- **INFO**: `tabs_presenter_ws_export_teardown._schedule_deferred_dispose`
  (`_on_export_finished`) —
  `websocket_stream_export_deferred_dispose_completed action=dispose_deferred`.
  Emitted when deferred disposal runs `deleteLater` after ownership ends.
- **WARNING**: `WebSocketStreamView.abandon_export_for_shutdown` —
  `websocket_stream_export_worker_finish_wait_timeout wait_ms=<int>
  action=export_abandoned`. `wait_ms` is the budget already spent before
  abandon (passed from the dispose helper) so queries match the defer WARNING
  field set.
- **EMERG / ALERT / CRIT / ERR / NOTICE / DEBUG**: none added for these paths.
  Existing PYPOST-1286 DEBUG finalize/stale events and INFO export
  start/complete events are unchanged.

### Not Logged (justified)

- Idle dispose (`outcome=disposed` without timeout) — happy path; no WARNING.
- Immediate race dispose after connect that returns `disposed` without staying
  deferred — avoids a misleading `action=dispose_deferred` WARNING; the page
  is already gone.
- Idempotent idle `abandon_export_for_shutdown` (worker is `None`) — silent
  return; idle teardown test asserts no `action=export_abandoned`.
- Transcript path/content on abandon/defer — avoided by design.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value`, `%`-style lazy formatting)
- Includes context: yes (`wait_ms`, `action`)
- Log levels: WARNING (timeout/defer/abandon), INFO (deferred dispose completed)
- No large data structures or export payloads in new events

## Metrics Implementation (if applicable)

Not applicable: desktop UI has no Prometheus/metrics backend for these paths.
Existing `record_teardown_metrics` on `TabsPresenter.teardown` is unchanged.

### Performance Metrics

- N/A

### Business Metrics

- N/A

### System Health Metrics

- N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A, desktop application)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [ ] Log aggregation (N/A; standard Python logging)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (caplog exact-prefix / field assertions)
- [ ] Metrics are collected correctly (N/A)
- [x] Logging works in error/timeout scenarios (busy defer + busy abandon)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring (N/A)

Tests: `tests/test_pypost_1301_observability.py` (module `pytestmark` timeout
30 s, bounded `Event.wait` / `wait_for_export`):

- `test_busy_tab_close_logs_dispose_deferred_then_completed` — one WARNING
  `action=dispose_deferred` with `wait_ms=`, then one INFO completed event
- `test_busy_teardown_logs_export_abandoned_with_wait_ms` — one WARNING
  `action=export_abandoned` with `wait_ms=`
- `test_idle_tab_close_skips_defer_and_abandon_logs` — neither action on idle
  close

Also retained: `test_idle_tabs_teardown_skips_export_abandon` in
`tests/test_pypost_1301_failing_repro.py`.

Commands:

- `make test PYTEST_ARGS="tests/test_pypost_1301_observability.py
  tests/test_pypost_1301_failing_repro.py -q"` — 2/2 files passed
- `make lint` — OK
- `make typecheck` — baseline OK (175 known errors)

## Notes

- Defer and abandon reuse the established
  `websocket_stream_export_worker_finish_wait_timeout` event name so existing
  finish-wait queries keep working; filter on `action=`.
- `wait_ms` on abandon was added in this step for field parity with defer and
  close_refused WARNINGs from PYPOST-1286.
