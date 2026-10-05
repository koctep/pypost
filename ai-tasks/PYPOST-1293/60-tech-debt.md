# PYPOST-1293: Technical Debt Analysis

## Shortcuts Taken

None. The test assertions for `test_keys_noop_without_tabs` and docstrings for
`TestCtrlReturnF5RoutingHttp` directly address the root technical debt item TD-6 identified
in `ai-tasks/PYPOST-1285/60-tech-debt.md`.

## Code Quality Issues

None introduced. All tests in `TestCtrlReturnF5RoutingHttp` conform to project test guidelines
with descriptive docstrings, explicit timeout markers via module-level `pytestmark`, and clean
assertions verifying empty-state behavior and logger contracts.

## Missing Tests

None for the scope of this task. Test coverage now explicitly verifies:
- `test_f5_sends_http_request`: verifies F5 triggers HTTP send when tab is active.
- `test_ctrl_return_sends_http_request`: verifies Ctrl+Return triggers HTTP send when tab is active.
- `test_keys_noop_without_tabs`: verifies F5 and Ctrl+Return with zero tabs do not alter tab count
  or active kind, and emit expected structured DEBUG log records.
- `test_routing_http_tests_conformance_and_docstrings`: verifies presence of docstrings and
  assertions.

## Performance Concerns

None. The test additions execute in milliseconds and have negligible impact on test runtimes.

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
