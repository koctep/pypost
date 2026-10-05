# PYPOST-1291: Technical Debt Analysis

## Shortcuts Taken

None. The dead facade methods (`handle_websocket_connect_global`,
`handle_websocket_send_message_global`, `handle_mcp_client_connect_global`, and
`handle_mcp_client_invoke_global`) were cleanly removed from `TabsPresenter`.
Active callers in `tests/test_main_window_hotkeys.py` were modernized to use `handle_f5_global`
and `handle_ctrl_return_global`, and the baseline metrics in
`ai-tasks/PYPOST-376/baseline-metrics.md` were updated and validated.

## Code Quality Issues

- Module-level route functions in `pypost/ui/presenters/tabs_presenter_hotkeys.py` are still named
  `handle_websocket_connect_global` and `handle_mcp_client_connect_global` even though their
  behavior toggles connection state. This is tracked in sprint task `PYPOST-1296`.
- `handle_websocket_format_json_global` remains as a facade on `TabsPresenter` because it is bound
  directly to `Ctrl+Shift+F` in `pypost/ui/main_window_protocol_hotkeys.py`. When format JSON is
  generalized across protocols, it can also transition to unified route tables.

## Missing Tests

None. Automated tests verify:
- Removal of the 4 dead facade methods (`TestTabsPresenterDeadFacadesRemoved`).
- Dispatching through `handle_f5_global()` and `handle_ctrl_return_global()` for WebSocket and
  MCP Client tabs.
- Baseline metrics tracking via `tests/test_solid_audit_baseline.py`.
All test methods have explicit timeout markers.

## Performance Concerns

None. Removing dead code reduces class size and dispatch lookup overhead.

## Follow-up Tasks

- `PYPOST-1296`: Public `WebSocketPresenter.toggle_connection()`; rename `*_connect_global`
  routers to toggle.
- `PYPOST-1292`: Share window-activation test helper between hotkey test modules.
- `PYPOST-1295`: `make` target to regenerate `ai-tasks/PYPOST-376/baseline-metrics.md`.

Pre-existing baseline test failures remain tracked under their respective existing Jira issues:
- **NON-BLOCKER — pre-existing**: `PYPOST-1261` (Malformed template expression classification in
  `tests/test_function_expression_resolver.py` and `tests/test_template_service.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1287` (Dialog inventory in
  `tests/test_pypost_1077_verification_artifacts.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1286` (WebSocket stream export in
  `tests/test_websocket_stream_view_repro.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1262` (Makefile and exit-policy timeouts in
  `tests/test_makefile_lifecycle.py`, `tests/test_makefile_targets.py`, and
  `tests/test_pytest_exit_policy.py`).
