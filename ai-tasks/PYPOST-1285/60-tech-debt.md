# PYPOST-1285: Technical Debt Analysis

Scope: the uncommitted PYPOST-1285 diff. Production code: `pypost/ui/hotkeys.py`,
`pypost/ui/main_window.py`, `pypost/ui/main_window_protocol_hotkeys.py`,
`pypost/ui/presenters/tabs_presenter.py`, `pypost/ui/presenters/tabs_presenter_hotkeys.py`.
Tests: `tests/test_main_window_hotkeys.py`, `tests/test_hotkeys.py`. Docs: `doc/user/hotkeys.md`,
`doc/user/websocket.md`. Snapshot: `ai-tasks/PYPOST-376/baseline-metrics.md`.

None of the items below block this task. The behavior in the Definition of Done (`10-requirements.md`)
is implemented and covered by tests.

## Shortcuts Taken

### TD-1: Outbound WebSocket messages are not counted

- **Description**: `Ctrl+Return` on a WebSocket tab routes to
  `WebSocketPresenter.handle_send_message`. That method only logs (`websocket_sending_message`
  DEBUG, `websocket_send_blocked_not_open` WARNING). The metric plumbing for outbound messages
  exists (`track_websocket_message` / `track_websocket_message_bytes` in `metrics_protocol.py`,
  `metrics_registry.py`, `metrics_otel.py`, `core/qt/metrics_websocket.py`), but no production
  code calls it. This gap is older than this task. This task made `Ctrl+Return` the main way to
  send from anywhere in the tab, which makes the gap more visible.
- **Location**: `pypost/ui/presenters/websocket_presenter.py` (`handle_send_message`) or the WS
  transport send path; metric definitions in `pypost/core/metrics_*.py` and
  `pypost/core/qt/metrics_websocket.py`.
- **Impact**: There is no metric for send volume or bytes per protocol. Dashboards cannot tell
  whether users send WS messages at all. Only the DEBUG `hotkey_routed` event shows it, and only
  for the hotkey path.
- **Priority**: Medium
- **Recommended follow-up**: Call `track_websocket_message` / `_bytes` (direction `out`) on a
  successful send. Add a contract test with a recording metrics tracker. Update the metrics
  catalog in `doc/dev/`.
- **Blocker**: no
- Jira: [PYPOST-1288](https://pypost.atlassian.net/browse/PYPOST-1288)

### TD-2: MCP client disconnect has no counter

- **Description**: `F5` on a connected MCP tab calls `McpClientPresenter.disconnect_requested`.
  This emits no metric. Connect (`track_mcp_client_connect`), list-tools and call-tool are
  counted.
- **Location**: `pypost/ui/presenters/mcp_client_presenter.py` (`disconnect_requested`) and
  the metrics protocol, registry, null tracker and OTel modules.
- **Impact**: The MCP session lifecycle metrics are asymmetric. Session duration and churn
  cannot be derived. WebSocket has `track_websocket_session_closed`; MCP has no equivalent.
- **Priority**: Medium
- **Recommended follow-up**: Add `track_mcp_client_disconnect` (with a reason label: user,
  error, teardown) through `MetricsTrackerProtocol`, the registry, the null tracker and OTel.
  Call it from the disconnect path. Add a test and update the docs.
- **Blocker**: no
- Jira: [PYPOST-1289](https://pypost.atlassian.net/browse/PYPOST-1289)

## Code Quality Issues

### TD-4: Uncalled `TabsPresenter` hotkey facade methods (pre-existing, kept by this diff)

- **Description**: The `TabsPresenter` facades `handle_websocket_connect_global`,
  `handle_mcp_client_connect_global` and `handle_mcp_client_invoke_global` had no production
  caller before this task either. At `HEAD` only `tests/test_main_window_hotkeys.py` called them.
  The old router `tabs_presenter_hotkeys.handle_send_request_global` called the module-level
  functions, not the facades. This diff keeps those three. It renames the pre-existing, already
  uncalled facade `handle_websocket_send_global` to `handle_websocket_send_message_global`, which
  no test calls either. It deletes `handle_mcp_client_send_global`. The net result is one fewer
  uncalled facade. Routing now goes `handle_f5_global` / `handle_ctrl_return_global` →
  module-level route tables in `tabs_presenter_hotkeys.py`.
- **Location**: `pypost/ui/presenters/tabs_presenter.py` (about lines 690–715).
- **Impact**: About 20 LOC of admission-gated wrappers in a module that is near its
  baseline-metrics cap (1073 / 1165). They also suggest wrong entry points: a new binding wired
  to them would skip the `hotkey_routed` log.
- **Priority**: Low
- **Recommended follow-up**: Remove the four remaining facades. Point the existing tests at
  `handle_f5_global` / `handle_ctrl_return_global` with the matching tab kind and state. Lower
  the `tabs_presenter.py` baseline.
- **Blocker**: no
- Jira: [PYPOST-1291](https://pypost.atlassian.net/browse/PYPOST-1291)

### TD-8: No `make` target regenerates the LOC baseline snapshot

- **Description**: `ai-tasks/PYPOST-376/baseline-metrics.md` is a hand-maintained LOC
  snapshot. `tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics`
  checks it. This task edited it twice (Step 4 iteration 5, Step 5). The only documented way to
  regenerate it is
  `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ...`, which calls a `.venv`
  binary directly. `AGENTS.md` forbids that ("make-only"), and the `Makefile` has no target for
  it.
- **Location**: `ai-tasks/PYPOST-376/baseline-metrics.md` ("Regenerate" section),
  `scripts/audit_baseline_metrics.py` (about line 220, which prints the same command),
  `Makefile`.
- **Impact**: Every task that changes `main_window.py` or a capped presenter has to edit the
  numbers by hand or break the project rule. Hand edits invite transcription errors and repeated
  test failures, as this task's Step 4 shows.
- **Priority**: Low
- **Recommended follow-up**: Add `make baseline-metrics` (regenerate) and optionally
  `make check-baseline-metrics`. Update the "Regenerate" text in the markdown and in
  `scripts/audit_baseline_metrics.py` to point at the target.
- **Blocker**: no
- Jira: [PYPOST-1295](https://pypost.atlassian.net/browse/PYPOST-1295)

### TD-9: Hotkey router calls a private presenter method; "connect" handlers actually toggle

- **Description**: `handle_websocket_connect_global` calls
  `ws_tab.presenter._on_connect_clicked()`, which is a private button slot of
  `WebSocketPresenter`. Tests patch the same private name. Both `handle_websocket_connect_global`
  and `handle_mcp_client_connect_global` toggle between connect and disconnect, but the names
  say "connect". The private call existed before this task; this task keeps it and builds the
  route tables on it.
- **Location**: `pypost/ui/presenters/tabs_presenter_hotkeys.py` (`handle_websocket_connect_global`,
  `handle_mcp_client_connect_global`); `pypost/ui/presenters/websocket_presenter.py`
  (`_on_connect_clicked`).
- **Impact**: The coupling to a private name means renaming the WS button slot silently breaks
  F5. The misleading names make the route tables harder to read.
- **Priority**: Low
- **Recommended follow-up**: Add a public `toggle_connection()` to `WebSocketPresenter`.
  Rename the routers to `handle_*_connect_toggle`. Update the tests to patch the public method.
- **Blocker**: no
- Jira: [PYPOST-1296](https://pypost.atlassian.net/browse/PYPOST-1296)

### Pre-existing flake8 E302 / E303 in tests (not a follow-up)

The test modules have older blank-line style deviations outside this diff. `make lint` runs flake8
on `pypost/` only, so `tests/` is not gated. This task did not add any. They are out of
scope and need no ticket.

## Missing Tests

Timeout markers (blocker-class check, `do-testing`): both touched test files declare a module
`pytestmark = pytest.mark.timeout(...)` (`tests/test_hotkeys.py` 30 s,
`tests/test_main_window_hotkeys.py` 120 s). **No blocker.**

### TD-3: No window-wide guard that each live key sequence is bound once

- **Description**: The latent bug fixed here was a display-only Help row (`QAction` with
  `setShortcut`) that made a real `QShortcut` ambiguous, so Qt fired neither. The current guards
  cover only part of that bug class:
  - `register_hotkey_documentation` no longer calls `setShortcut`. This is a structural fix for
    that helper.
  - `TestProtocolSessionHelpRows::test_documentation_rows_bind_no_shortcut` checks only the
    rows from `register_protocol_session_hotkeys`.
  - `TestMainWindowSendKeyWiring::test_no_documentation_row_binds_a_key` (F4) classifies an
    action as "documentation" when it has `receivers(triggered) == 0`. That heuristic also
    matches `register_hotkey_group` rows (such as "Send Request" and Alt+1..9), whose real
    bindings are separate `QShortcut` objects the test never inspects.
  - The F5 / Ctrl+Return / Ctrl+L slot-count tests protect only those three keys.

  Two cases are not caught:
  1. Two real bindings with the same key, for example a future `register_hotkey(..., "F5")` in
     another section. Both would be `QShortcut` or `QAction` objects with receivers, so F4
     skips them.
  2. A display row made with plain `tag_action(keys=...)` (which still calls `setShortcut`) on
     an action that later gets a receiver.
- **Location**: `tests/test_main_window_hotkeys.py` (`TestMainWindowSendKeyWiring`),
  `pypost/ui/hotkeys.py` (`tag_action`, `register_hotkey`, `register_hotkey_group`).
- **Impact**: A future hotkey could silently disable an existing one. Users would see this as
  "the key does nothing", with no error or log, which is the same symptom as the bug fixed here.
- **Priority**: Medium
- **Recommended follow-up**: Add one window-level test on a real `MainWindow`. It collects
  every live key sequence from `findChildren(QShortcut)` plus every `QAction.shortcut()` with
  the same context (window or application), then asserts there are no duplicates. Optionally,
  connect `activatedAmbiguously` in `register_hotkey*` to a WARNING log
  (`hotkey_ambiguous key=...`) so the runtime case is visible.
- **Blocker**: no
- Jira: [PYPOST-1290](https://pypost.atlassian.net/browse/PYPOST-1290)

### TD-5: Duplicated window-activation test helpers

- **Description**: `tests/test_hotkeys.py::_ActivatedWindow` (`activate` / `click`) and
  `tests/test_main_window_hotkeys.py::TestMainWindowSendKeyWiring` (`_activate` / `_click`)
  repeat the same show → `activateWindow` → `QTest.qWaitForWindowActive(2000)` → skip →
  `setFocus` → `processEvents` sequence. The `_ACTIVATION_SKIP` constant is defined in both
  modules.
- **Location**: `tests/test_hotkeys.py` (about lines 90–130), `tests/test_main_window_hotkeys.py`
  (about lines 664 and 752–768).
- **Impact**: The two copies can drift, for example if the timeout or skip policy changes in only
  one. The next real-key-event test would add a third copy.
- **Priority**: Low
- **Recommended follow-up**: Move the helper into a shared test helper (`tests/conftest.py`
  fixture or `tests/helpers/qt_activation.py`) and use it from both modules.
- **Blocker**: no
- Jira: [PYPOST-1292](https://pypost.atlassian.net/browse/PYPOST-1292)

### TD-6: `test_keys_noop_without_tabs` has no assertion; HTTP group tests lack docstrings

- **Description**: `TestCtrlReturnF5RoutingHttp::test_keys_noop_without_tabs` presses F5 and
  Ctrl+Return with no tabs and asserts nothing after the presses. It passes as long as nothing
  raises. The three tests in `TestCtrlReturnF5RoutingHttp` are the only routing tests without
  one-line docstrings. Every other group added in this task has them.
- **Location**: `tests/test_main_window_hotkeys.py` (`TestCtrlReturnF5RoutingHttp`, about
  lines 468–500).
- **Impact**: The test checks less than its name says. A regression that, for example, opens a
  new tab or calls a handler on F5 with no tabs would not be caught. The missing docstrings are
  only a style inconsistency.
- **Priority**: Low
- **Recommended follow-up**: Assert `active_tab_kind() is None` and the tab count after the
  presses. Assert the `hotkey_routed ... tab_kind=none action=noop` log (or reuse the
  `TestHotkeyRoutedLogging` no-tab case and delete this test). Add docstrings.
- **Blocker**: no
- Jira: [PYPOST-1293](https://pypost.atlassian.net/browse/PYPOST-1293)

### TD-7: F6 Help-row snapshot assumes Linux key names; display formats are mixed

- **Description**: `_EXPECTED_OTHER_HELP_ROWS` (`test_other_help_rows_unchanged`) is a literal
  snapshot with Linux and Windows key text (`Ctrl+Q`, `Ctrl+Return`, ...). Documentation rows
  now store native text (`QKeySequence(k).toString(NativeText)`), so on macOS the WebSocket and
  MCP "Send Message" / "Invoke Tool" rows show `⌘↩` and the snapshot fails.
  `register_hotkey_group` and `tag_action` alt-keys store raw strings, so on macOS the
  "Send Request" row stays `F5 / Ctrl+Return`. The Help dialog then mixes native and portable
  text (acknowledged in `20-architecture.md`). CI is ubuntu-only, so CI does not catch this.
- **Location**: `tests/test_main_window_hotkeys.py` (`_EXPECTED_OTHER_HELP_ROWS`,
  `test_other_help_rows_unchanged`); `pypost/ui/hotkeys.py` (`register_hotkey_group`,
  `tag_action`, `register_hotkey_documentation`).
- **Impact**: macOS developers see a local test failure. macOS users see inconsistent shortcut
  text in Help → Hotkeys.
- **Priority**: Low
- **Recommended follow-up**: Normalize every displayed key to NativeText in one place, either in
  `collect_hotkey_rows` or in the three registration helpers. Build the snapshot expectation
  through the same `QKeySequence(...).toString(NativeText)` conversion, or mark it
  Linux-only with an explicit `skipif`.
- **Blocker**: no
- Jira: [PYPOST-1294](https://pypost.atlassian.net/browse/PYPOST-1294)

## Performance Concerns

None. Routing is a dictionary lookup on the active tab kind plus one DEBUG log call. It does no
I/O and runs once per keypress. The removed focus-walk (`_is_descendant`) was the only loop.

## Follow-up Tasks

### New follow-ups (unticketed; orchestrator to create and backfill)

| ID | Title | Priority | Blocker | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Count outbound WebSocket messages (`track_websocket_message[_bytes]`) | Medium | no | Jira: [PYPOST-1288](https://pypost.atlassian.net/browse/PYPOST-1288) |
| TD-2 | Add MCP client disconnect counter | Medium | no | Jira: [PYPOST-1289](https://pypost.atlassian.net/browse/PYPOST-1289) |
| TD-3 | Window-wide guard: each live key sequence bound once (+ ambiguous-activation log) | Medium | no | Jira: [PYPOST-1290](https://pypost.atlassian.net/browse/PYPOST-1290) |
| TD-4 | Remove uncalled `TabsPresenter` hotkey facade methods | Low | no | Jira: [PYPOST-1291](https://pypost.atlassian.net/browse/PYPOST-1291) |
| TD-5 | Share window-activation test helper between hotkey test modules | Low | no | Jira: [PYPOST-1292](https://pypost.atlassian.net/browse/PYPOST-1292) |
| TD-6 | Add assertions to `test_keys_noop_without_tabs`; docstrings for HTTP group | Low | no | Jira: [PYPOST-1293](https://pypost.atlassian.net/browse/PYPOST-1293) |
| TD-7 | Platform-neutral Help-row snapshot; NativeText for all displayed keys | Low | no | Jira: [PYPOST-1294](https://pypost.atlassian.net/browse/PYPOST-1294) |
| TD-8 | `make` target to regenerate `ai-tasks/PYPOST-376/baseline-metrics.md` | Low | no | Jira: [PYPOST-1295](https://pypost.atlassian.net/browse/PYPOST-1295) |
| TD-9 | Public WS `toggle_connection()`; rename `*_connect_global` routers to toggle | Low | no | Jira: [PYPOST-1296](https://pypost.atlassian.net/browse/PYPOST-1296) |

### Pre-existing test failures (NON-BLOCKER — pre-existing, already filed; not refiled)

Seen during Steps 3–6 full `make test` runs. Each one reproduces with this task's edits stashed,
or times out or crashes when run alone. None is caused by this diff.

- **NON-BLOCKER — pre-existing**: resolver / template malformed-nested failures and environment
  widget process crashes.
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
  - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
  - `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
  - `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
  - `tests/test_environment_list_widget.py`, `tests/test_environment_export_ui.py` (process
    crash, exit -7 / -11)
  - Jira: [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261)
- **NON-BLOCKER — pre-existing**: Makefile / pytest-policy suites hit the 120 s worker timeout,
  even when run alone.
  - `tests/test_makefile_lifecycle.py`
  - `tests/test_makefile_targets.py`
  - `tests/test_pytest_exit_policy.py`
  - Jira: [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262)
- **NON-BLOCKER — pre-existing (flaky)**: these fail under load and pass alone.
  - `tests/test_websocket_stream_view_repro.py::test_stream_view_transcript_export_actions`
  - `tests/test_template_service.py::TestTemplateServiceRenderString::test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`
  - Jira: [PYPOST-1286](https://pypost.atlassian.net/browse/PYPOST-1286)
- **NON-BLOCKER — pre-existing**: the PYPOST-1077 dialog audit LOC snapshot is out of date.
  - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  - Jira: [PYPOST-1287](https://pypost.atlassian.net/browse/PYPOST-1287)

### Carried to Step 8 (this task, no ticket)

- Add the `hotkey_routed` DEBUG event to the `doc/dev/logging.md` event catalog (deferred from
  Step 6).
- Document in `doc/dev/` the rule that display-only Help rows must use
  `register_hotkey_documentation` and never `tag_action(keys=...)` or `register_hotkey`. This
  reduces the risk from TD-3 until that guard test exists.
