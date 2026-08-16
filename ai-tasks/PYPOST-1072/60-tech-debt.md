# PYPOST-1072: Technical Debt Analysis

## Shortcuts Taken

No temporary production shortcut was found. The implementation separates the migration result
from the inherited `QThread.finished()` lifecycle signal and retains the worker until bounded
termination cleanup, as designed.

The timing-sensitive native failure was not converted into a direct crash-reproduction test.
Instead, the task uses a deterministic ownership-ordering test and real Qt worker tests. This is
an intentional testing seam from the approved architecture, not undisclosed debt.

## Code Quality Issues

No new actionable code-quality issue was found in the scoped implementation.

- `MigrationOperation` constrains the two accepted operations, and the public `operation`
  property avoids new test or logging access to private state.
- `_WORKER_FINISH_WAIT_MS` names the cleanup policy rather than embedding a literal in control
  flow. Its 100 millisecond value matches the established collection, environment, and import
  worker cleanup pattern.
- The host dialog's `_migration_worker` compatibility field remains an existing encapsulation
  compromise. The approved architecture intentionally preserves it to keep this lifecycle fix
  minimal; PYPOST-1072 does not worsen that coupling.

## Missing Tests

No timeout-marker blocker exists. Both changed test modules declare explicit module-level
timeouts: 30 seconds for the worker tests and 120 seconds for the Qt UI tests. The UI helper also
uses an assertion-producing 5,000 millisecond internal bound.

One non-blocking coverage gap remains: the deterministic lifecycle fake exercises the success
ordering and cleanup-timeout paths, but not the sequence `failed(message)` followed by inherited
`finished()`. The direct worker tests cover exception-to-`failed` emission, and the production
failure handler is unchanged apart from deferring ownership release, so this gap does not block
the lifecycle fix. A focused UI test would protect the failure dialog, retained ownership, and
button restoration as one contract.

## Performance Concerns

No unbounded wait remains in the changed lifecycle path. The GUI-thread cleanup join is capped at
100 milliseconds and occurs only after Qt emits thread completion. A false return produces a
structured warning, releases ownership, and restores controls. This bounded, rare maintenance
path does not require optimization for this task.

The full suite completed twice on the unchanged Step 4 implementation, in 549.51 seconds and
547.88 seconds of pytest time. Running additional repeated full suites could increase statistical
confidence about a timing-sensitive native failure, but it is optional validation rather than a
real blocker, missing acceptance condition, or technical-debt task.

## Architecture Deviations

None found. The implementation follows the approved signal split, explicit lifecycle ownership,
bounded cleanup, deterministic seam test, assertion-producing Qt wait, and minimal-change scope.
No production dependency or user-visible migration behavior was added.

## Hardcoded Values

No actionable hardcoded-value debt was found.

- `100` milliseconds is centralized in `_WORKER_FINISH_WAIT_MS` and follows existing repository
  worker-cleanup policy.
- `5_000` milliseconds is the explicit inner test wait bound and is independently capped by the
  module's pytest timeout.

## Blocker Assessment

- **BLOCKERS:** None.
- **NON-BLOCKER:** The five baseline failures below predate PYPOST-1072 and are deduplicated to
  Jira [PYPOST-1071](https://pypost.atlassian.net/browse/PYPOST-1071).
- **OPTIONAL CONFIDENCE:** More repeated full-suite runs may further sample timing behavior, but
  the two equivalent completed runs already satisfy the requirement. Additional repetition is
  not a blocker or mandatory follow-up.

## Follow-up Tasks

- **NON-BLOCKER — missing test:** Add deterministic UI coverage for `failed(message)` before
  inherited `finished()`, proving that the worker remains retained until lifecycle completion,
  the failure result is displayed, and migration buttons are restored afterward.
  Jira: [PYPOST-1078](https://pypost.atlassian.net/browse/PYPOST-1078) (2 points).

The exact five baseline node IDs are all **NON-BLOCKER — pre-existing** and deduplicated to Jira
[PYPOST-1071](https://pypost.atlassian.net/browse/PYPOST-1071):

```text
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_main_window_class_loc_within_cap
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_main_window_file_loc_within_cap
tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics
tests/test_verify_ai_task_artifacts.py::TestCommittedBaseline::test_baseline_matches_current_scan
```

## Validation Results

- Focused worker and settings migration validation passed: 14 tests in 0.20 seconds.
- Markdown whitespace validation passed with `git diff --check`.
- Follow-up coverage was ticketed after blocker review as
  [PYPOST-1078](https://pypost.atlassian.net/browse/PYPOST-1078).
