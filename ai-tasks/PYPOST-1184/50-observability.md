# PYPOST-1184: Observability Implementation

## Logging Implementation

### Added Logs

None. No new logging was added by this refactor.

### Existing Logging (unchanged, reviewed for consistency)

This task is a pure internal refactor: it extracts the previously-triplicated
"insert tab before plus / append+ensure-plus / focus / optionally save state"
sequence out of `add_new_tab`, `_insert_mcp_client_tab`, and
`_insert_websocket_tab` (in `pypost/ui/presenters/tabs_presenter.py`) into a
single free function `insert_tab_before_plus` in the new
`pypost/ui/presenters/tabs_presenter_insert.py`. No behavior, control flow, or
log output changed — the three call sites still call the same operations in
the same order, just via the shared helper.

Reviewed the existing logging conventions in `tabs_presenter.py` and its
sibling `tabs_presenter_*.py` helper modules before deciding whether to add
logs to the new helper:

- **`tabs_presenter_close.py`** (`close_workspace_tab`, extracted in
  PYPOST-1159, the closest structural sibling to this extraction — a single
  per-tab UI mechanic pulled out of `TabsPresenter`): has **no** `logging`
  import and **no** log calls at all. Single-tab open/close mechanics are not
  logged at that layer.
- **`tabs_presenter_request_close.py`**, **`tabs_presenter_ws_close.py`**,
  **`tabs_presenter_mcp_close.py`**: each logs exactly one `logger.info(...)`
  call, but only for the *bulk cascading close driven by external deletion*
  (e.g. `close_tabs_for_deleted_requests closed_count=%d request_ids=%s`) —
  a business-meaningful aggregate event, not the per-tab mechanic.
- **`tabs_presenter.py`** itself already logs tab-lifecycle events one layer
  above the insert mechanic, at the call sites that matter for
  diagnostics/telemetry: `handle_new_tab` logs
  `new_tab_action_triggered`/`new_tab_action_completed`/
  `new_tab_action_cancelled`; `restore_tabs` logs
  `restore_tabs_completed restored_count=%d` (and
  `restore_tabs_no_saved_tabs opened_blank_tab=true`); `load_request_from_history`
  logs `history_request_loaded_into_editor`. `open_blank_tab` also emits the
  `track_gui_new_tab_action` metric. These already cover the "a tab was
  opened, from where, why" observability need for every caller of
  `insert_tab_before_plus`.

Given `insert_tab_before_plus` is a mechanical QTabWidget operation
(index lookup, insert/append, focus, optional state save) with the exact same
sibling precedent (`close_workspace_tab`) already established as unlogged,
and every one of its three call sites is already covered by
caller-level logging or metrics, adding a log line inside the new helper
would duplicate existing signal and violate the "do not over-instrument a
pure refactor" guidance for this step. No logging was added.

### Log Structure

- Structured logs: n/a (no logs added)
- Includes context: n/a
- Log levels used elsewhere in this file/module family: `DEBUG`, `INFO`,
  `WARNING`, `ERROR` (standard Python `logging`, mapped informally to
  syslog-style severities; no `EMERG`/`ALERT`/`CRIT` usage in this module
  family, consistent with a desktop GUI presenter layer).

## Metrics Implementation (if applicable)

Not applicable. No new metrics were added. Existing metrics
(`self._metrics.track_gui_new_tab_action`, etc.) are emitted by the callers of
`insert_tab_before_plus`, not by the helper itself, and were untouched by this
refactor.

## Monitoring Integration

- [ ] Prometheus metrics — n/a, not used by this desktop app's presenter layer
- [ ] Grafana dashboards — n/a
- [ ] Alerting rules — n/a
- [ ] Log aggregation (ELK, Loki, etc.) — n/a

## Validation Results

- [x] Logs are correctly formatted — n/a, none added; existing caller-level
  logs unchanged (verified by inspection, no diff to their call sites)
- [x] Metrics are collected correctly — n/a, none added
- [x] Logging works in error scenarios — n/a, no new error paths introduced
- [x] Large data structures are not logged — n/a
- [ ] Metrics are available for monitoring — n/a, no monitoring backend in
  this desktop app

## Notes

This step intentionally made no code changes. Verified no regressions by
re-running the targeted test files:

- `tests/test_tabs_presenter_insert.py`
- `tests/test_tabs_presenter.py`

Both pass, confirming the (unchanged) logging/metrics behavior around tab
insertion still functions as before the Step 4 refactor.
