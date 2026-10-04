# Roadmap: PYPOST-1285

## Task Metadata

- **Implementation language**: Python (PySide6/Qt desktop app `pypost`; user documentation in
  Markdown)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1285/00-roadmap.md`
  - `ai-tasks/PYPOST-1285/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1285/20-architecture.md` — key-specific routers (`handle_f5_global`,
    `handle_ctrl_return_global`), focus-independent routing, display-only Help rows fix
    (latent ambiguous-shortcut defect), Step 3 red-test plan (groups A–F)
  - Fix pass after review: Ctrl+L / doc-row collision audit (F5, Ctrl+Return, Ctrl+L), WS
    `OPEN`-state cases, mandatory window activation for E/F, DoD 1–17 traceability table,
    Qt doc source links
  - Fix pass 2: verified `MainWindow` close strategy (override `_shutdown_for_exit`), WS blank
    tab state `SessionState.IDLE`
- [x] **STEP 3: Failing Repro Test**
  - Test files: `tests/test_main_window_hotkeys.py` (groups A–D, F; `_press` fallback helper,
    `patch.object(QApplication, "focusWidget")` focus control), `tests/test_hotkeys.py` (group E).
    Timeouts inherited from module `pytestmark` (120 s / 30 s). No production or `doc/` edits.
  - Run: `make test PYTEST_ARGS='tests/test_main_window_hotkeys.py tests/test_hotkeys.py -v'` →
    20 red (intended), 12 new guards green, all 20 pre-existing tests in both files green.
  - Window activation: `QTest.qWaitForWindowActive(w, 2000)` returned `True` offscreen; **no
    recorded skips**. Group F kept (offscreen `MainWindow` stable); close via
    `_shutdown_for_exit` override, `not isVisible()` asserted. `_create_menu_bar` is **not**
    patched in group F so the snapshot covers "Quit Application".
  - A `TestCtrlReturnF5RoutingWebSocket` (blank WS tab, `SessionState.IDLE`; `OPEN` via
    `_current_state`):
    - RED `test_ctrl_return_outside_composer_sends_not_toggles` — Connect toggled (1 != 0)
    - RED `test_ctrl_return_with_no_focus_sends_not_toggles` — Connect toggled
    - RED `test_ctrl_return_disconnected_does_not_connect` — `handle_connect` called
    - RED `test_f5_in_composer_toggles_not_sends` — message sent
    - RED `test_ctrl_return_open_outside_composer_does_not_disconnect` — session disconnected
    - RED `test_f5_open_in_composer_disconnects_not_sends` — message sent
    - green guards: `test_ctrl_return_in_composer_sends`, `test_f5_outside_composer_toggles`,
      `test_ctrl_return_open_in_composer_sends_not_disconnects`,
      `test_f5_open_outside_composer_disconnects`
  - B `TestCtrlReturnF5RoutingMcpClient`:
    - RED `test_ctrl_return_outside_invoke_form_invokes_not_toggles` — Connect toggled
    - RED `test_ctrl_return_connected_outside_form_does_not_disconnect` — disconnected
    - RED `test_f5_in_invoke_form_toggles_not_invokes` — tool invoked
    - RED `test_f5_connected_in_invoke_form_disconnects` — tool invoked
    - green guard: `test_ctrl_return_in_invoke_form_invokes`
  - C `TestCtrlReturnF5RoutingHttp` (regression guards, green): `test_f5_sends_http_request`,
    `test_ctrl_return_sends_http_request`, `test_keys_noop_without_tabs`
  - D `TestProtocolSessionHelpRows`:
    - RED `test_websocket_connect_row_lists_only_f5` / `test_mcp_connect_row_lists_only_f5` —
      `'F5 / Ctrl+Return' != 'F5'`
    - RED `test_no_key_listed_twice_within_session_sections` — `Ctrl+Return` duplicated
    - RED `test_documentation_rows_bind_no_shortcut` — six doc rows bind F5 / Ctrl+Return / Ctrl+L
    - green guard: `test_send_and_invoke_rows_list_native_ctrl_return`
  - E `tests/test_hotkeys.py`:
    - RED `test_documentation_row_does_not_make_bound_shortcut_ambiguous` — F5 slot count 0
      (ambiguous overload)
    - RED `test_focus_url_ctrl_l_not_ambiguous_with_protocol_doc_rows` — Ctrl+L count 0 (Alt+D
      guard passes first)
    - green guard: `test_documentation_row_displays_native_text`
  - F `TestMainWindowSendKeyWiring` (real `MainWindow`, `MagicMock` tabs, real key events):
    - RED `test_f5_key_dispatches_f5_router_once` — `handle_f5_global` 0 calls
    - RED `test_ctrl_return_key_dispatches_ctrl_return_router_once` — 0 calls
    - RED `test_ctrl_l_and_alt_d_reach_handle_focus_url` — Ctrl+L 0 calls (Alt+D guard OK)
    - RED `test_no_documentation_row_binds_a_key` — six doc rows bind keys
    - green guards: `test_send_request_help_row_unchanged`, `test_other_help_rows_unchanged`
      (literal snapshot of today's rows minus WS/MCP "Connect / Disconnect"; Linux native text)
  - Full `make test`: only the two files above fail from this change. Unrelated failures (they
    reproduce with this step's test edits stashed, or time out when run alone):
    `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
    `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`,
    `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`,
    `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`,
    `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`
    `tests/test_template_service.py::TestTemplateServiceRenderString::test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`,
    `tests/test_environment_export_ui.py` / `tests/test_environment_list_widget.py` (process crash
    exit -7/-11), `tests/test_makefile_lifecycle.py`, `tests/test_makefile_targets.py`,
    `tests/test_pytest_exit_policy.py` (120 s worker timeout even when run alone);
    `tests/test_websocket_stream_view_repro.py::test_stream_view_transcript_export_actions`
    flaky under load (passes alone)
- [x] **STEP 4: Development**
  - [x] Iteration 1 — registry fix (`pypost/ui/hotkeys.py`): `register_hotkey_documentation`
    no longer calls `setShortcut`; it stores every key as native text in `ALT_KEYS_PROPERTY`.
    Documentation rows cannot make F5 / Ctrl+Return / Ctrl+L ambiguous. Group E green.
  - [x] Iteration 2 — key-specific routing: `tabs_presenter_hotkeys.py` adds `handle_f5_global`,
    `handle_ctrl_return_global`, `handle_websocket_send_message_global`, `_send_http_request`
    (routing by active tab kind only); removes `handle_send_request_global`,
    `handle_websocket_send_global`, `handle_mcp_client_send_global`, `_focus_in_composer`,
    `_focus_in_invoke_form`, `_is_descendant` and the `QApplication` / `QWidget` import.
    `TabsPresenter` facade wrappers replaced the same way (admission-gated).
    `main_window.py` binds "Send Request" via `register_hotkey_group` (F5 → `handle_f5_global`,
    Ctrl+Return → `handle_ctrl_return_global`, `collapse_keys=False`).
    `main_window_protocol_hotkeys.py`: WS / MCP "Connect / Disconnect" → `("F5",)`, docstring.
  - [x] Iteration 3 — tests per architecture plan step 7: removed the `_press` fallback branch
    (Step 3 helper, marked "removed in Step 4"); pre-existing
    `test_{websocket,mcp_client}_session_documentation_rows_registered` use `keys=("F5",)`.
    No Step 3 assertion changed.
  - [x] Iteration 4 — user docs: `doc/user/hotkeys.md` (WS / MCP Connect / Disconnect = `F5`;
    Send Message / Invoke Tool work anywhere in the tab), `doc/user/websocket.md` (Connect:
    `F5`; Send: `Ctrl+Enter` without focus condition). `doc/user/mcp-client.md` has no key
    mentions — unchanged. `doc/dev/` left for Step 8.
  - [x] Iteration 5 — `ai-tasks/PYPOST-376/baseline-metrics.md` snapshot: `main_window.py` file
    LOC 456 → 459, `MainWindow` class LOC 408 → 411 (caps 477 / 426 unchanged), fixing
    `tests/test_solid_audit_baseline.py::test_markdown_snapshot_matches_current_metrics`.
  - Results: `make test PYTEST_ARGS='tests/test_main_window_hotkeys.py tests/test_hotkeys.py -v'`
    → both files fully green (all 20 Step 3 red tests now pass). `make lint` OK, `make typecheck`
    OK (mypy baseline 181). `make check` / full `make test`: 349 files, failures only in the
    documented pre-existing set (PYPOST-1261, -1262, -1286, -1287); solid-audit snapshot fixed
    in iteration 5 and re-run green.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1285/40-code-cleanup.md`
  - Added docstrings to the `TabsPresenter` facade methods `handle_f5_global`,
    `handle_ctrl_return_global` and `handle_websocket_send_message_global` (Step 4 reviewer
    note). `ai-tasks/PYPOST-376/baseline-metrics.md`: `tabs_presenter.py` LOC 1070 → 1073
    (cap 1165).
  - Test hygiene: replaced the stale "RED today" / "green today" docstrings and the "Step 3"
    banners in `tests/test_main_window_hotkeys.py` and `tests/test_hotkeys.py`. Assertions
    are unchanged.
  - No unused imports, dead code or lines over 100 characters found. No behavior change.
  - `make lint` OK, `make typecheck` OK (baseline 181), targeted `make test` (4 files) passed.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1285/50-observability.md`
  - DEBUG event `hotkey_routed key=<f5|ctrl_return> tab_kind=<...> action=<...>` in
    `pypost/ui/presenters/tabs_presenter_hotkeys.py` (`_log_hotkey_routed`, route tables
    `_F5_ACTIONS` / `_CTRL_RETURN_ACTIONS`); no tab → `tab_kind=none action=noop`. No metrics
    added. No behavior change.
  - Contract tests: `tests/test_main_window_hotkeys.py::TestHotkeyRoutedLogging` (4 tests).
  - `main_window.py` / `tabs_presenter.py` unchanged, so baseline-metrics needs no update.
  - `make lint` OK, `make typecheck` OK (baseline 181), targeted `make test` (3 files) passed.
  - `doc/dev/logging.md` catalog entry for `hotkey_routed` is deferred to Step 8 (Dev Docs).
  - Fix pass (review FAIL): route tables replaced by `_F5_ROUTES` / `_CTRL_RETURN_ROUTES`
    (`TabProtocol` → `(label, handler)`), dispatched by `_dispatch`; event logged after the
    handler runs, early return → `action=noop reason=target_unavailable`. Corrected the
    downstream-coverage claim: WS send-message and MCP disconnect have no counter; recorded both
    under "Follow-up for Step 7" in `50-observability.md`. Tests: Ctrl+Return no-tab, early-return
    noop, route-table coverage (7 tests in `TestHotkeyRoutedLogging`). `main_window.py` /
    `tabs_presenter.py` unchanged.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1285/60-tech-debt.md`: 9 new follow-ups (TD-1…TD-9), none blocking.
    Medium: TD-1 outbound WS send counter, TD-2 MCP disconnect counter, TD-3 window-wide
    live-shortcut uniqueness guard (F4 guards only cover display-only rows). Low: TD-4 dead
    `TabsPresenter` facade methods, TD-5 duplicated activation helpers, TD-6 assertion-free
    `test_keys_noop_without_tabs` + missing docstrings, TD-7 Linux-only F6 snapshot / mixed
    native vs. raw key text, TD-8 no `make` target for baseline-metrics regeneration, TD-9
    private `_on_connect_clicked` call + "connect" handlers that toggle.
  - Timeout markers: both touched test files carry module `pytestmark` timeouts (30 s / 120 s)
    — no blocker.
  - Pre-existing failures recorded NON-BLOCKER with Jira keys: PYPOST-1261, PYPOST-1262,
    PYPOST-1286, PYPOST-1287 (already filed; not refiled).
  - No code, test or `doc/` changes in this step.
  - Fix pass: TD-4 reworded (facades were already uncalled at `HEAD`; diff renamed one, removed one); TD-8 moved into body, TD items reordered.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hotkeys.md`: replaced the removed `handle_send_request_global` example (Focus URL
    Bar for `register_hotkey`, "Send Request" for `register_hotkey_group` with
    `collapse_keys=False`). New sections: "Documentation-only rows (display, never bind)" (rule,
    Qt ambiguous-shortcut reason, guard tests, PYPOST-1290 / PYPOST-1294), "Send key routing
    (F5 / Ctrl+Return)" (`_dispatch` over `_F5_ROUTES` / `_CTRL_RETURN_ROUTES`, focus-independent,
    `True`/`False` handler contract, PYPOST-1296), and "Behavior change (PYPOST-1285)" for release
    notes (the project keeps no changelog under `doc/`).
  - `doc/dev/websocket_hotkeys.md`, `doc/dev/mcp_client_hotkeys.md`: routing tables and API
    rewritten to the new model: F5 = connect toggle, Ctrl+Return = send / invoke; removed
    `handle_*_send_global` and focus wording; links to `hotkeys.md`, `logging.md`, PYPOST-1296.
  - `doc/dev/logging.md`: `hotkey_routed` DEBUG row in "UI actions" (covers both "Carried to
    Step 8" items from `60-tech-debt.md`).
  - Grep of `doc/` for removed names (`handle_send_request_global`,
    `handle_websocket_send_global`, `handle_mcp_client_send_global`, `_focus_in_composer`,
    `_focus_in_invoke_form`, `_is_descendant`) now returns no matches. No production or test
    changes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1285/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1285/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1285/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1285/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1285/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
