# PYPOST-1285: Observability Implementation

## Logging Implementation

### Conventions Reviewed

- Project style: `logger = logging.getLogger(__name__)` per module, snake_case event name
  followed by `key=value` pairs (for example `new_tab_action_triggered source=%s`,
  `request_send_rejected reason=teardown`, `websocket_send_blocked_not_open`).
- Before this task, no hotkey routing module logged anything. The removed focus-dependent router
  (`handle_send_request_global`, `_focus_in_composer`, `_focus_in_invoke_form`) emitted no log
  events, so nothing needed a replacement.
- Downstream coverage of the routed actions is uneven (see the coverage table below): HTTP send,
  WebSocket connect / disconnect, MCP connect and MCP invoke are counted; WebSocket send-message
  and MCP disconnect are only logged or not observed at all.

### Added Logs

- **DEBUG**: `pypost/ui/presenters/tabs_presenter_hotkeys.py` — `_dispatch` calls
  `_log_hotkey_routed` for `handle_f5_global` and `handle_ctrl_return_global`. Each keypress
  emits exactly one event, **after** the handler has run, so it reports what actually happened:

  ```text
  hotkey_routed key=<f5|ctrl_return> tab_kind=<http|websocket|mcp_client|none> action=<...> [reason=<...>]
  ```

  | key | tab_kind | action | reason |
  | --- | --- | --- | --- |
  | `f5` | `websocket`, `mcp_client` | `connect_toggle` | — |
  | `f5` | `http` | `send_request` | — |
  | `ctrl_return` | `websocket` | `send_message` | — |
  | `ctrl_return` | `mcp_client` | `invoke_tool` | — |
  | `ctrl_return` | `http` | `send_request` | — |
  | any | `none` | `noop` | — |
  | any | any kind | `noop` | `target_unavailable` |

  `reason=target_unavailable` is logged when the handler returns early without acting (for
  example a WebSocket tab whose `presenter` is `None`, or the active widget no longer matching
  the resolved kind). Route handlers return `True` when they ran their action.
- **Single source of truth**: `_F5_ROUTES` / `_CTRL_RETURN_ROUTES` map each `TabProtocol` to
  `(label, handler)`, and `_dispatch` dispatches from the table. The label cannot drift from the
  handler, and the lookup uses `routes.get(kind)`, so logging can never raise before dispatch.
  `test_route_tables_cover_every_tab_kind` asserts both tables cover every `TabProtocol` value;
  the no-tab case is handled before the lookup. `tab_kind` reuses the `TabProtocol` values,
  which already match the metrics `protocol` labels.
- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO**: none added. "No active tab" is a
  normal state, not a fault. A WARNING there would add noise, so it is DEBUG `action=noop`. The
  "not OPEN" and "not connected" guards keep their existing logs and UI messages.

### Log Structure

- Structured logs: yes (`event key=value`)
- Includes context: yes (key, active tab kind, action actually run, noop reason)
- Log levels: DEBUG
- No URLs, payloads, headers or other user data are logged. Only fixed enum strings appear.

## Metrics Implementation (if applicable)

### Performance Metrics

- N/A: routing is a constant-time dispatch with no I/O.

### Business Metrics

- None added. Downstream coverage of each routed action:

  | key | tab_kind | action | downstream metric |
  | --- | --- | --- | --- |
  | `f5`, `ctrl_return` | `http` | `send_request` | `track_request_sent` |
  | `f5` | `websocket` | `connect_toggle` | `track_websocket_session_opened` / `_start_refused` (connect), `track_websocket_session_closed` (disconnect) |
  | `f5` | `mcp_client` | `connect_toggle` | `track_mcp_client_connect` (connect); **none** for disconnect |
  | `ctrl_return` | `websocket` | `send_message` | **none** — `WebSocketPresenter.handle_send_message` only logs (`websocket_sending_message` DEBUG, `websocket_send_blocked_not_open` WARNING) |
  | `ctrl_return` | `mcp_client` | `invoke_tool` | `track_mcp_client_call_tool` |

  `track_websocket_message` / `track_websocket_message_bytes` exist
  (`metrics_protocol.py`, `metrics_registry.py`, `metrics_otel.py`,
  `core/qt/metrics_websocket.py`) but no production code calls them. Adding counters here would
  touch `MetricsTrackerProtocol`, the registry, the null tracker and the metrics docs, all
  outside this ticket's scope. The DEBUG event is enough to diagnose routing.

### System Health Metrics

- N/A

## Monitoring Integration

- [ ] Prometheus metrics (not applicable; see above)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation: the standard `pypost` log pipeline, DEBUG level

## Validation Results

- [x] Logs are correctly formatted. Contract tests in `tests/test_main_window_hotkeys.py::
  TestHotkeyRoutedLogging` (`assertLogs` at DEBUG on
  `pypost.ui.presenters.tabs_presenter_hotkeys`) check the exact message for WS, MCP and HTTP
  with both keys, the no-tab `noop` case for both keys, the early-return
  `noop reason=target_unavailable` case, and route-table coverage of every `TabProtocol`.
- [x] Metrics are collected correctly (unchanged; none added)
- [x] Logging works in edge scenarios (no active tab → `action=noop`; handler returned early →
  `action=noop reason=target_unavailable`)
- [x] Large data structures are not logged
- [x] No behavior change: the same handler runs for each tab kind (table dispatch replaces the
  `if/elif`); the log call runs after dispatch and cannot raise. Existing Step 3/4 routing tests
  pass unchanged.
- `make lint` OK, `make typecheck` OK (baseline 181),
  `make test PYTEST_ARGS='tests/test_main_window_hotkeys.py tests/test_hotkeys.py
  tests/test_solid_audit_baseline.py'` → 3/3 files passed.

## Notes

- `main_window.py` and `tabs_presenter.py` are unchanged in this step (fix pass included), so
  `ai-tasks/PYPOST-376/baseline-metrics.md` needs no update.
- The `TabsPresenter` facade returns early when admission is closed (teardown) without logging.
  That matches the other hotkey facade methods and is left as is.
- The `doc/dev/logging.md` event catalog entry for `hotkey_routed` is deferred to Step 8 (Dev
  Docs).

## Follow-up for Step 7

Tech-debt candidates (not implemented here, out of scope):

- **Outbound WebSocket message counter**: wire `track_websocket_message` /
  `track_websocket_message_bytes` into `WebSocketPresenter.handle_send_message` (or the
  transport send path). The metric plumbing exists but has no production caller.
- **MCP client disconnect counter**: `McpClientPresenter.disconnect_requested` (reached via F5
  on a connected MCP tab) emits no metric; connect, list-tools and call-tool do.
