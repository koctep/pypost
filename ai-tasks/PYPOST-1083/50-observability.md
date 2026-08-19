# PYPOST-1083: Observability Implementation

## Summary

This task is a pure internal-cleanup: `_open_mcp_servers` in
`pypost/ui/presenters/mcp_controls_presenter.py` already logged
`"mcp_servers_dialog_opened server_count=%d"` at INFO before Step 4. Step 4 only changed
*how* the count is computed — from `len(controller.mcp_server_configurations())` (which
deep-copies every persisted `McpServerConfiguration` row via `model_copy(deep=True)`) to
`controller.mcp_server_count()` (a trivial `len(self._settings.mcp_servers)` with no
copying and no logging of its own). No new observable behavior was introduced, so Step 6
is a verification pass, not a build pass — consistent with the task's own framing
("verify rather than invent new instrumentation").

## Logging Implementation

### Existing Log Verified Unchanged

- **INFO**: `pypost/ui/presenters/mcp_controls_presenter.py:292-295`
  (`McpControlsPresenter._open_mcp_servers`) — `"mcp_servers_dialog_opened server_count=%d"`.
  - **Level**: unchanged (`logger.info`, matches the sibling dialog-open logs
    `mcp_activity_dialog_opened` and `mcp_tools_overview_opened` in the same class).
  - **Message text**: unchanged (`"mcp_servers_dialog_opened server_count=%d"`).
  - **Semantics**: unchanged — the value logged is still "number of configured MCP server
    rows at dialog-open time"; only the source of that integer changed
    (`controller.mcp_server_count()` instead of
    `len(controller.mcp_server_configurations())`). Field name (`server_count`) and value
    are identical for the same underlying settings state.
  - **Cost**: cheaper — the new path is `len()` over the settings list with no per-row
    `model_copy(deep=True)`, so the log statement's own execution no longer forces an
    O(n) deep copy of every server configuration just to report a count.

- **No new logging added inside `mcp_server_count()`**
  (`pypost/ui/mcp_server_controller.py:122-124`) — confirmed intentional per the accepted
  Step 4 diff description ("no logging inside it; it's a trivial len() accessor"). A
  trivial length accessor logging on every call would itself be log noise disproportionate
  to its significance, so this is correct per the "do not output large data structures /
  only meaningful fields" guidance — there is no meaningful *new* event here, only an
  internal accessor.

### Log Structure

- Structured logs: yes (`key=value` token style, consistent with the rest of
  `mcp_controls_presenter.py`, e.g. `mcp_active_env_changed prev_env_id=%s new_env_id=%s`,
  `mcp_server_started host=%s port=%d`).
- Includes context: yes — `server_count` is the single relevant field for this event; no
  server names, ports, endpoint IDs, or other row-level details are logged (unchanged from
  before Step 4 — this event was already a count-only summary, per the inline comment at
  the call site: "The sibling dialogs already log their open with a count; this one is
  also the single entry point for every `mcp_servers_persist_requested` mutation below
  it").
- Log levels used (this call site only): INFO.

## Metrics Implementation

Not applicable. This change touches a single log statement's input computation; no
performance/business/system-health metric was added, changed, or removed. A new
counter/metric for "MCP servers dialog opened" was considered and rejected: the existing
INFO log already serves this purpose, `_metrics: MetricsTrackerProtocol` calls elsewhere in
this class exist for genuinely trend-worthy events (e.g. `track_mcp_active_env_changed()`
in `track_active_env_changed`), and dialog-open counts are not currently tracked as a
metric anywhere in the codebase — adding one here would be scope creep unrelated to the
stated fix (stopping an unnecessary deep copy).

## Monitoring Integration

- [ ] Prometheus metrics — N/A, no metrics touched
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — unaffected; log format/level/text unchanged, so
      existing aggregation queries/dashboards keyed on `mcp_servers_dialog_opened` or
      `server_count=` continue to match without modification.

## Validation Results

- [x] Logs are correctly formatted — verified by reading
  `pypost/ui/presenters/mcp_controls_presenter.py:283-311`: same `logger.info(...)` call,
  same format string, only the argument's source expression changed.
- [x] Metrics are collected correctly — N/A (no metrics in scope); confirmed no metrics
  call sites reference `mcp_server_count`/`mcp_server_configurations` for this event.
- [x] Logging works in error scenarios — the `controller is None` branch
  (`logger.warning("mcp_servers_dialog_no_controller")`) is untouched by this task and its
  test (`test_open_mcp_servers_without_controller_logs_warning`) still passes.
- [x] Large data structures are not logged — confirmed: only an `int` (`server_count`) is
  logged, both before and after Step 4; the full configuration list itself was never
  logged, so this task neither introduces nor removes a large-payload logging risk.
- [x] No regression: targeted test suite
  (`PYTEST_ARGS="tests/test_mcp_controls_presenter.py -v" make test`) — 6 passed, 0
  failed. Specifically
  `test_open_mcp_servers_with_controller_logs_info_and_constructs_dialog` asserts
  `"mcp_servers_dialog_opened server_count=2" in caplog.text` at `caplog.at_level(logging.INFO)`,
  `controller.mcp_server_count.assert_called_once()`, and
  `controller.mcp_server_configurations.assert_not_called()` — i.e. the log line's output is
  verified byte-for-byte identical while the expensive call path is verified to no longer
  run.
- [x] No other call sites reference this log line or the changed methods outside
  `pypost/ui/presenters/mcp_controls_presenter.py`,
  `pypost/ui/mcp_server_controller.py`, and their two test modules (confirmed via
  repo-wide grep for `mcp_servers_dialog_opened` and `mcp_server_count`).

## Notes

- This is a Step-6 verification pass, not a Step-6 build pass: the task's own framing
  ("a new counter/metric is very unlikely to be warranted; verify rather than invent new
  instrumentation") is confirmed correct after inspection — no new logging or metrics were
  warranted or added.
- `mcp_server_count()` itself (`pypost/ui/mcp_server_controller.py:122-124`) intentionally
  has no logging, per the accepted Step 4 diff; this is appropriate for a private,
  high-frequency-safe accessor with no side effects worth recording on every call.
