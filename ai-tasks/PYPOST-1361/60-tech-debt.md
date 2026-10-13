# PYPOST-1361: Technical Debt Analysis

## Shortcuts Taken

None. The refreshed snapshots (`ai-tasks/PYPOST-376/baseline-metrics.md` and
`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`) reflect actual, current source code AST structures
and line counts. No shortcuts or temporary crutches were introduced:
- Refreshed snapshots strictly reflect actual current source code AST and line counts.
- No architectural caps (`FILE_CAPS` or `MAIN_WINDOW_CLASS_CAP`) were raised or modified.
- No contract assertions, diff checks, or verification constraints were relaxed, bypassed,
  or removed.

## Code Quality Issues

None. No code quality issues, style violations, or formatting compromises exist:
- Verified clean formatting and valid GitHub-Flavored Markdown table syntax.
- Verified line lengths in all modified documents are strictly <= 100 characters.
- Static analysis quality gates pass cleanly (`make lint`, flake8, markdown lint, link check).
- Physical module LOC and class line counts remain within caps (`make check-baseline-metrics`).

## Missing Tests

None. Automated regression test suites fully cover snapshots and drift detection:
- `tests/test_solid_audit_baseline.py`:
  `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
- `tests/test_pypost_1077_verification_artifacts.py`:
  `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
- `tests/test_pypost_1287_failing_repro.py`:
  `test_live_report_inventory_loc_matches_discovery`

All test files declare explicit timeout markers conforming to repository testing standards
(`@pytest.mark.timeout(...)` or module-level `pytestmark`), and bounded execution limits
are strictly observed.

## Performance Concerns

None. Snapshot verification and generation take < 4 seconds across all three regression test
suites. Parsing is performed via fast AST scanning and line counting in memory.

## Follow-up Tasks

No new implementation follow-up tasks are required for this ticket.

The following pre-existing test failures and issues remain in the repository and are tracked
as separate open backlog issues in Sprint 2026:

### PYPOST-1363: Repair flake8 default reporter discovery in isolated Make fixtures

**NON-BLOCKER — pre-existing** — [PYPOST-1363][pypost-1363]. Two baseline failures raise flake8
`KeyError: 'default'` when discovering entry points in isolated Make fixtures:
```text
tests/test_makefile_exit_behavior.py::
  TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test
tests/test_makefile_target_filtering.py::TestTargetFiltering::test_lint_succeeds_after_install
```
This is an open backlog Debt issue in Sprint 2026.

### PYPOST-1306: Flaky under parallel load: run_parallel_tests grandchild process-group timeout

**NON-BLOCKER — pre-existing** — [PYPOST-1306][pypost-1306]. Flaky test failure under parallel
worker load when the 1.0s timeout expires before grandchild PID is recorded:
```text
tests/test_run_parallel_tests.py::test_worker_timeout_terminates_grandchild_process_group
```
This is an open backlog Debt issue in Sprint 2026.

[pypost-1363]: https://pypost.atlassian.net/browse/PYPOST-1363
[pypost-1306]: https://pypost.atlassian.net/browse/PYPOST-1306
