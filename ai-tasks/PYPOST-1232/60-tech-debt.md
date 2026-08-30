# PYPOST-1232: Technical Debt Analysis

## Shortcuts Taken

None. This is a 1-story-point, test-only assertion fix (`envelope.v == 1` -> `== 2` in
`tests/test_environment_export.py`) with no production code change.

## Code Quality Issues

None identified in the changed line or its surrounding test.

## Missing Tests

None — the fixed test already exercises the full export/import round trip with an encrypted
(v2) envelope. No new coverage gap was introduced or discovered by this task.

## Performance Concerns

None.

## Follow-up Tasks

Pre-existing, already-tracked failures observed during the Step 4 full-suite run
(`make test`, 304/311 files passed, 6 pre-existing failures — none caused by this task):

- `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir` —
  NON-BLOCKER — pre-existing. Jira: [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233)
- `tests/test_main_window_alert_reload.py` (segfault, exit code -11) —
  NON-BLOCKER — pre-existing. Jira: [PYPOST-1251](https://pypost.atlassian.net/browse/PYPOST-1251)
- `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  (dialog inventory/LOC drift, mcp_servers_dialog.py now 446 LOC) —
  NON-BLOCKER — pre-existing. Jira: [PYPOST-1252](https://pypost.atlassian.net/browse/PYPOST-1252)
  (also tracked under [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111))
- `tests/test_makefile.py` (whole-file worker timeout at 120s under parallel load) —
  NON-BLOCKER — pre-existing. Jira: [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234)
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
  and `::test_markdown_snapshot_matches_current_metrics` (`pypost/core/template_service.py`
  241 LOC exceeds the 225 cap; snapshot drift) —
  NON-BLOCKER — pre-existing. Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)
  (both node ids already present in that issue's comment history)
- `tests/test_pytest_exit_policy.py::test_make_test_fails_with_exit_code_5_when_no_tests_collected`
  (`subprocess.TimeoutExpired` on an internal `make install` call under parallel-suite CPU
  contention) — NON-BLOCKER — pre-existing, same root-cause cluster as PYPOST-1234. Recorded
  as a comment on [PYPOST-1234](https://pypost.atlassian.net/browse/PYPOST-1234) (no new
  Jira issue filed — deduped against the existing Makefile-timeout-under-load cluster).

All six pre-existing failures/clusters above are linked to existing sprint 1979 Jira issues;
no new Jira issue was required for this task's Phase D.
