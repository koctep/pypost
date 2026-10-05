# PYPOST-1294: Technical Debt Analysis

## Shortcuts Taken

None. The implementation cleanly addresses TD-7 from `ai-tasks/PYPOST-1285/60-tech-debt.md`.
All key strings retrieved from `ALT_KEYS_PROPERTY` are now normalized through
`QKeySequence(key).toString(NativeText)` in `_keys_from_action`, and test expectations in
`tests/test_main_window_hotkeys.py` dynamically build native expectations.

## Code Quality Issues

None introduced. All modules follow PEP 8 and project style conventions with lines <= 100
characters. Centralizing `NativeText` formatting in `_keys_from_action` ensures that any future
callers adding alternative keys or groups will automatically produce native formatting without
needing custom conversion logic.

## Missing Tests

None for this task's scope.
- `tests/test_hotkeys.py::test_collect_hotkey_rows_formats_all_keys_with_native_text` verifies
  that primary shortcuts, alternative shortcuts, and grouped shortcuts all format through
  `NativeText`.
- `tests/test_main_window_hotkeys.py::TestMainWindowSendKeyWiring::test_other_help_rows_unchanged`
  verifies the entire live window help row snapshot using platform-neutral conversion.
- All tests carry explicit timeout markers.

## Performance Concerns

None. Transforming short strings through `QKeySequence` occurs only when opening Help → Hotkeys
or running test snapshots, incurring sub-millisecond execution times.

## Follow-up Tasks

No new follow-up tasks required from this change.

Pre-existing test failures in the repository are tracked under existing Jira issues:
- `NON-BLOCKER — pre-existing`: Coverage gate drops below 85% on `make test-cov` (tracked in
  PYPOST-1261).
- `NON-BLOCKER — pre-existing`:
  `tests/test_storage.py::test_storage_init_creates_default_request_when_no_active_requests`
  fails due to mock storage state behavior (tracked in PYPOST-1287).
- `NON-BLOCKER — pre-existing`:
  `tests/test_mcp_client_tab.py::TestMcpClientTabUiWiring::test_initial_form_hidden_and_populated_on_connect`
  and
  `tests/test_mcp_client_tab.py::TestMcpClientTabUiWiring::test_refresh_button_triggers_reconnect`
  fail on Qt event loop timings (tracked in PYPOST-1286).
- `NON-BLOCKER — pre-existing`:
  `tests/test_collection_runner.py::TestCollectionRunnerIntegration::test_runner_runs_entire_collection`
  fails in isolated runner execution (tracked in PYPOST-1262).
