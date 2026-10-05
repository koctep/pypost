# PYPOST-1296: Technical Debt Analysis

## Shortcuts Taken

None. The implementation cleanly resolves TD-9 from `ai-tasks/PYPOST-1285/60-tech-debt.md`.
`WebSocketPresenter.toggle_connection()` is a fully supported public method, and
`_on_connect_clicked()` delegates directly to it as a Qt button slot. Router functions in
`tabs_presenter_hotkeys.py` are renamed to `handle_websocket_connect_toggle` and
`handle_mcp_client_connect_toggle`, aligning function names with the `action=connect_toggle`
dispatch and logging table while retaining backward-compatibility aliases.

## Code Quality Issues

None introduced. All changes in `pypost/ui/presenters/websocket_presenter.py`,
`pypost/ui/presenters/tabs_presenter_hotkeys.py`, and `tests/test_main_window_hotkeys.py`
strictly follow PEP 8 and project style conventions with lines <= 100 characters.

## Missing Tests

None for this task's scope.
- `tests/test_main_window_hotkeys.py::TestWebSocketToggleConnectionAndRouterNaming::test_websocket_presenter_exposes_public_toggle_connection`
  verifies that `WebSocketPresenter` exposes a callable public `toggle_connection()` method.
- `tests/test_main_window_hotkeys.py::TestWebSocketToggleConnectionAndRouterNaming::test_router_functions_renamed_to_toggle`
  verifies that `tabs_presenter_hotkeys` defines both `handle_websocket_connect_toggle` and
  `handle_mcp_client_connect_toggle`, and binds them to `_F5_ROUTES`.
- Existing integration tests verify runtime toggle execution and logging.
- All tests carry explicit timeout markers.

## Performance Concerns

None. Method delegation and router renaming carry zero runtime performance overhead.

## Follow-up Tasks

No new follow-up tasks required from this change.

Pre-existing test failures in the repository are tracked under existing Jira issues:
- `NON-BLOCKER — pre-existing`: Parser error classification drift and Qt SIGSEGV teardown
  crashes (`tests/test_function_expression_resolver.py`, `tests/test_template_service.py`,
  `tests/test_environment_list_widget.py`, `tests/test_environment_export_ui.py`,
  `tests/test_ui_actions.py`) tracked in PYPOST-1261.
- `NON-BLOCKER — pre-existing`: Parallel worker timeouts under full-suite load in
  `tests/test_makefile_lifecycle.py`, `tests/test_makefile_targets.py`, and
  `tests/test_pytest_exit_policy.py` tracked in PYPOST-1262.
- `NON-BLOCKER — pre-existing`: Flaky test failures under parallel load:
  `tests/test_websocket_stream_view_repro.py::test_stream_view_transcript_export_actions`
  and
  `tests/test_template_service.py::TestTemplateServiceRenderString::test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`
  tracked in PYPOST-1286.
- `NON-BLOCKER — pre-existing`: Stale dialog LOC inventory in
  `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  tracked in PYPOST-1287.
