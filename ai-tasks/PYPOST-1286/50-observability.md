# PYPOST-1286: Observability Implementation

## Logging Implementation

All new events use the module logger `pypost.ui.widgets.websocket.stream_view` and the
repository's structured `event_name key=value` convention (same style as the existing
`websocket_stream_export_*` events and the `*_worker_finish_wait_timeout` events in
`collection_import_actions.py` and the storage gateways).

### Added Logs

- **WARNING**: `WebSocketStreamView.closeEvent` —
  `websocket_stream_export_worker_finish_wait_timeout wait_ms=<int> action=close_refused`.
  Emitted when `cleanup()` cannot finish export teardown within `_WORKER_FINISH_WAIT_MS`
  (100 ms) and the close is refused. Restores the event removed in Step 4 (same name, so
  existing log queries keep working); `action=close_refused` records the new behavior
  (close is refused instead of disposing an owned worker).
- **DEBUG**: `WebSocketStreamView._finalize_export_worker` —
  `websocket_stream_export_worker_finalize_deferred retry_ms=<int>`. Emitted once per worker
  when `QThread.finished` arrived but the nonblocking native join is not ready yet. Retries
  run every `_FINALIZE_RETRY_MS` (10 ms), so only the first deferral is logged to avoid
  flooding DEBUG output.
- **DEBUG**: `WebSocketStreamView._finalize_export_worker` —
  `websocket_stream_export_worker_finalized deferrals=<int>`. Emitted when ownership is
  released and the worker is scheduled for deletion; `deferrals` counts the join retries,
  which makes the race this task fixed measurable in DEBUG traces.
- **DEBUG**: `WebSocketStreamView._on_export_worker_finished` —
  `websocket_stream_export_worker_finished_ignored reason=stale_worker`. Emitted when a
  finished notification does not come from the currently owned worker. Harmless by design
  (the identity check is a guard), hence DEBUG rather than WARNING.
- **EMERG / ALERT / CRIT / ERR / NOTICE / INFO**: none added. Existing INFO
  (`websocket_stream_export_started`, `_completed`, `_skipped`) and ERROR
  (`websocket_stream_<format>_export_failed`) events are unchanged.

### Not Logged (justified)

- `TemplateService.clear_cache()` and `FunctionRegistry.reset()` — test-isolation hooks
  with no production caller, no failure mode, and no input parameters. A log would add noise
  to every test teardown without diagnostic value.
- `wait_for_export()` timeouts — a public synchronization helper whose `False` result is the
  contract; callers decide severity. The only production caller (`closeEvent` via
  `cleanup()`) logs the WARNING above.
- Retry-path identity mismatch inside `_finalize_export_worker` — only reachable if
  ownership changed between retries, which only finalization itself does; silent return is
  correct.

### Log Structure

- Structured logs: yes (`event_name key=value`, `%`-style lazy formatting)
- Includes context: yes (wait budget, retry interval, deferral count, ignore reason)
- Log levels: WARNING, DEBUG
- No sensitive data: no paths, payloads, environment values, or exception text in new events

## Metrics Implementation (if applicable)

Not applicable: the desktop application has no metrics backend. The `deferrals` field on
`websocket_stream_export_worker_finalized` serves as a log-derived indicator of join delay.

### Performance Metrics

- N/A

### Business Metrics

- N/A

### System Health Metrics

- N/A

## Monitoring Integration

- [ ] Prometheus metrics (N/A, desktop application)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [ ] Log aggregation (N/A; standard Python logging)

## Validation Results

- [x] Logs are correctly formatted (exact-message caplog assertions)
- [ ] Metrics are collected correctly (N/A)
- [x] Logging works in error scenarios (refused close with blocked worker)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring (N/A)

Tests: `tests/test_pypost_1286_observability.py` (module `pytestmark` timeout 30 s, bounded
`Event.wait`/`QEventLoop` waits):

- `test_close_refused_logs_finish_wait_timeout_warning` — one WARNING on refused close,
  none on the later accepted close, one `finalized` DEBUG.
- `test_finalize_deferral_logs_once_and_reports_retry_count` — one `finalize_deferred`
  DEBUG across several retries, then `finalized deferrals>=1`.
- `test_stale_worker_finished_signal_logs_debug_and_keeps_ownership` — ignored DEBUG and
  ownership retained.

Commands (all via `make`):

- `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1286_observability.py
  tests/test_pypost_1286_failing_repro.py tests/test_template_service.py
  tests/test_websocket_stream_view_repro.py -q'` — 4/4 files passed; observability file
  re-run twice more, passed.
- `make lint` — OK.
- `make typecheck` — OK, 181 baseline errors (no regression).

## Notes

- New module constant `_FINALIZE_RETRY_MS = 10` replaces the literal retry interval so the
  code and the log field share one value.
- `_finalize_export_worker` gained an internal `deferrals: int = 0` parameter carried through
  the `QTimer.singleShot` retry lambda; existing callers are unaffected.
