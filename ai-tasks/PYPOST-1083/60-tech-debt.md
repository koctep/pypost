# PYPOST-1083: Technical Debt Analysis

## Shortcuts Taken

None. The change is a minimal, single-purpose accessor added to the existing
`McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`) and to the
`McpServerController` Protocol (`pypost/ui/presenters/mcp_controls_presenter.py`), swapping the
`_open_mcp_servers` dialog-open log call from `len(controller.mcp_server_configurations())`
(deep-copies every row via `model_copy(deep=True)`) to `controller.mcp_server_count()`
(`len(self._settings.mcp_servers)`, no copying). No temporary workaround, no scope creep, no
behavior change to the log line's level, message, or format — verified in Step 6
(`ai-tasks/PYPOST-1083/50-observability.md`).

## Code Quality Issues

None found. The new method follows the exact style of its neighbors in
`McpServerSettingsController` (short docstring, direct one-line body) and the Protocol addition
follows the existing `def ...: ...` stub convention in `McpServerController`. `mcp_server_count()`
is the only concrete implementer of the new Protocol member and `_open_mcp_servers` is the only
call site — checked via repo-wide grep for other classes/mocks structurally typed against
`McpServerController`; none exist besides the one `MagicMock(spec=McpServerController)` in
`tests/test_mcp_controls_presenter.py`, which the Step 3/4 diff already updated.

## Missing Tests

- `mcp_server_count()` has no dedicated unit test in `tests/test_mcp_server_controller.py`
  exercising the real `McpServerSettingsController` against actual settings data. Its sibling
  method `mcp_server_configurations()` has one
  (`test_mcp_server_controller_configurations_returns_deep_copies`), but the new method is
  currently verified only indirectly, through the presenter test's mocked controller
  (`tests/test_mcp_controls_presenter.py::test_open_mcp_servers_with_controller_logs_info_and_constructs_dialog`,
  which asserts `controller.mcp_server_count.assert_called_once()` and
  `controller.mcp_server_configurations.assert_not_called()`). The implementation is a one-line
  `len(...)` delegation, so risk is low, but coverage is asymmetric with the established pattern
  in that test file. Not a blocker for this tiny fix; worth a follow-up test if
  `McpServerSettingsController` gets touched again.

All tests in the touched files declare module-level `pytestmark = pytest.mark.timeout(30)`
(confirmed in both `tests/test_mcp_controls_presenter.py` and
`tests/test_mcp_server_controller.py`) — no BLOCKER per `do-testing`.

## Performance Concerns

None new. This change *removes* a performance concern (an O(n) deep-copy of every
`McpServerConfiguration` row, including nested Pydantic models, done solely to compute a count
for a log line) and replaces it with an O(1)-amortized `len()` call. `mcp_server_configurations()`
itself still deep-copies on every call at its other call sites (e.g. dialog construction) — that
is intentional (callers need independent, mutable copies) and out of scope for this task.

## Follow-up Tasks

- `test_cli_re_encrypt_dry_run`, `test_cli_re_encrypt_dry_run_json_includes_reencrypt_stats`,
  `test_cli_re_encrypt_reports_reencrypt_stats`,
  `test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden` /
  `test_bulk_re_encrypt_dry_run_projects_active_kid` (flaky, order-dependent) —
  NON-BLOCKER — pre-existing. Confirmed failing identically at baseline commit `2b770ada` and at
  HEAD during Step 4's full-suite run; unrelated to this task's files. 3 new node ids added as a
  comment on existing Jira issue
  [PYPOST-1088](https://pypost.atlassian.net/browse/PYPOST-1088).
- `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
  `test_markdown_snapshot_matches_current_metrics` —
  NON-BLOCKER — pre-existing. Confirmed failing identically at baseline and HEAD during Step 4's
  full-suite run; unrelated to this task's files. Jira:
  [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) (new Debt issue, 3 SP).
- `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication` —
  NON-BLOCKER — pre-existing. Confirmed failing identically at baseline and HEAD during Step 4's
  full-suite run; unrelated to this task's files. Jira:
  [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110) (new Debt issue, 1 SP).

No new follow-up tasks are needed for this task's own change. The optional `mcp_server_count()`
direct-unit-test gap noted under "Missing Tests" is low-risk (one-line `len()` delegation) and is
not being filed as a separate Jira issue — it can be picked up opportunistically the next time
`McpServerSettingsController` is touched.
