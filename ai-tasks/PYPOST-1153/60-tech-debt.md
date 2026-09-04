# PYPOST-1153: Technical Debt Analysis

## Scope and Verdict

This analysis reviews the requirements, architecture, implementation, tests, cleanup report,
observability report, repository guidance, and Jira context for PYPOST-1153.

The seven requested parallel-runner follow-ups are implemented and have focused automated
coverage. No blocker or high-severity debt was found. The remaining items are bounded design
trade-offs and verification gaps that are acceptable for this task. The known full-suite
failures are pre-existing and remain classified under PYPOST-1261 and PYPOST-1262; no duplicate
Jira issues are needed.

## Shortcuts Taken

1. The runner retains the inline `python -c` worker wrapper and `os._exit()` shutdown behavior
   from the earlier runner. This avoids known pytest/plugin shutdown hangs, but keeps a custom
   subprocess boundary and adds interpreter startup work for every dispatched file.
2. The implementation keeps compatibility projections such as `TestResult`, `RunResult.test_file`,
   and the `all_target_records` dispatch parameter. They preserve existing consumers while the
   new layout and result contracts settle, but they increase the supported surface.
3. Coverage cleanup removes runner-owned root `.coverage.*` fragments and the root `.coverage`
   file before a coverage run. This prevents stale data from contaminating an aggregate result,
   but assumes root coverage data belongs to this workflow.

## Code Quality Issues

### 1. Pytest private parser API and replay logic

- **Severity:** Medium residual maintainability risk.
- **Location:** `scripts/run_parallel_tests.py:290-318` and `:493-670`.
- **Impact:** Lossless ordering requires a second replay scan after `argparse.parse_known_args()`.
  That scan loads pytest and plugin options through private internals such as
  `_preparse`, `_parser._getparser`, and `_ensure_unconfigure`. A pytest or plugin upgrade can
  therefore break discovery or change option classification before any test is scheduled.
- **Mitigation:** Keep pytest major versions pinned by the project, isolate the private access in
  one adapter, and add a compatibility test/matrix when a new pytest major is adopted. Preserve
  the existing ordered-argv and sentinel contract tests.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, intentionally retained by the accepted architecture. Future Jira follow-up
  is recommended when the supported pytest range changes; no ticket is created in this step.

### 2. Compatibility result and dispatch surface

- **Severity:** Low.
- **Location:** `scripts/run_parallel_tests.py:173-220`, `:966-993`, and `:912-921`.
- **Impact:** The runner supports both the historical `TestResult` shape and the newer
  `RunResult` shape. `build_child_argv()` accepts `all_target_records` without currently using
  it, and `discover_test_files()` remains a path-only compatibility projection. Future changes
  can update one projection while leaving another subtly inconsistent.
- **Mitigation:** Keep compatibility tests while downstream consumers migrate, then deprecate
  the unused projections and simplify the dispatch protocol in a separately reviewed change.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, deliberate compatibility debt; no separate Jira issue is required yet.

### 3. Coverage cleanup has destructive ownership assumptions

- **Severity:** Low operational risk.
- **Location:** `scripts/run_parallel_tests.py:76-92` and `:1173-1183`.
- **Impact:** The runner deletes root `.coverage` and root `.coverage.*` files to isolate its
  aggregate run. A developer's serial coverage data in the root location could be removed, and
  an unlink failure is only reported as a warning. The dedicated `.coverage_parallel` directory
  reduces contamination risk but does not remove this ownership ambiguity.
- **Mitigation:** Document the root-file ownership contract, prefer the dedicated coverage path
  for all runner operations, and consider preserving unrelated root `.coverage` data or failing
  closed when cleanup cannot complete.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, low-priority hardening candidate; not a new Jira ticket for this task.

### 4. Coverage failure classification is output-format dependent

- **Severity:** Low observability risk.
- **Location:** `scripts/run_parallel_tests.py:30-50`.
- **Impact:** Threshold and configuration categories are inferred from coverage.py text with
  regular expressions. A future coverage.py wording change can turn a threshold failure into a
  generic report failure, reducing diagnostic precision, although the non-zero result still
  fails the run.
- **Mitigation:** Keep the aggregate exit-code contract independent of classification, add
  versioned output fixtures when coverage.py changes, and use a more structured coverage API if
  the project needs stable machine-readable categories.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, non-blocking observability debt; no immediate Jira follow-up.

## Missing Tests and Verification Gaps

### 1. Pytest-version compatibility coverage

- **Severity:** Medium verification gap coupled to Code Quality Issue 1.
- **Impact:** The focused suite validates the current installed pytest option schema, but does not
  exercise the runner against multiple supported pytest/plugin versions.
- **Mitigation:** Add a CI compatibility job or a documented version matrix before widening the
  dependency range. No production behavior change is required for this task.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Deferred; covered by the Code Quality Issue 1 follow-up candidate.

### 2. CI summary execution is not an end-to-end test

- **Severity:** Low.
- **Location:** `.github/workflows/test.yml:181-213` and
  `tests/test_parallel_runner_followups_repro.py:497-506`.
- **Impact:** The test verifies that the workflow references `CoverageManager` and
  `_read_project_policy`, but does not execute the GitHub Actions shell/Python summary block.
  A YAML quoting or runner-import change could therefore affect the summary without being caught
  locally.
- **Mitigation:** Keep the summary small and add a Make-driven fixture or CI syntax/execution
  check if the summary logic grows. The actual coverage exit gate remains enforced by the runner
  and `coverage report`.
- **Owner:** CI maintainers.
- **Status:** Deferred, non-blocking; no immediate Jira follow-up.

### 3. Default discovery remains intentionally shallow

- **Severity:** Low.
- **Location:** `scripts/run_parallel_tests.py:815-838` and `:846-859`.
- **Impact:** Default discovery selects `tests/test_*.py`, and directory targets expand the
  immediate directory pattern. A future nested test layout needs explicit targets or additional
  discovery behavior, otherwise new tests may not run in the standard command.
- **Mitigation:** Keep the current flat-layout contract documented; add a recursive-discovery
  requirement and tests before changing repository test layout.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Accepted scope limitation; no Jira follow-up unless the test layout changes.

## Performance Concerns

### 1. Per-file interpreter startup overhead

- **Severity:** Low.
- **Impact:** Each test file starts an isolated Python/pytest process. This preserves Qt fault
  isolation and makes per-file timeouts enforceable, but increases cumulative CPU and startup
  overhead.
- **Mitigation:** Operators should continue to tune `WORKERS` for available memory and suite
  duration.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, non-blocking performance debt; no new Jira ticket is required.

### 2. Aggregate coverage combination cost

- **Severity:** Low.
- **Impact:** Coverage combines all worker fragments only after the worker pool completes. Large
  suites can retain many fragments and delay the final report, although the dedicated directory
  and cleanup prevent stale root data from being included.
- **Mitigation:** Keep the dedicated coverage directory and cleanup behavior; monitor aggregate
  runtime as the suite grows.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, non-blocking performance debt; no new Jira ticket is required.

### 3. Fixed worker timeout for environment-heavy tests

- **Severity:** Medium.
- **Impact:** The fixed Make default of `WORKER_TIMEOUT=120` is a practical compatibility
  default, but not a universal budget for virtual-environment-heavy test files.
- **Mitigation:** Tune the worker timeout for environment-heavy suites and address the broader
  timeout behavior through the existing PYPOST-1262 investigation.
- **Owner:** Test-infrastructure maintainers.
- **Status:** Open, non-blocking pre-existing performance debt tracked by PYPOST-1262; no
  duplicate Jira ticket is needed.

## Pre-existing Test Failures

These failures are explicitly outside PYPOST-1153 scope and are not new debt from this change.
They must not be refiled or duplicated.

### NON-BLOCKER — pre-existing — PYPOST-1261

Jira: [PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261)

- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::`
  `test_malformed_nested_expressions`
- `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::`
  `test_standalone_malformed_closing_paren`
- `tests/test_environment_list_widget.py::<module>` — historical parallel-worker SIGSEGV
  (`-11`); individual node attribution is unavailable.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::`
  `test_markdown_snapshot_matches_current_metrics`
- `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::`
  `test_validate_malformed_nested_alignment`
- `tests/test_template_service.py::TestTemplateServiceObservability::`
  `test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`

The full gate evidence recorded for this task reproduced the two resolver failures, the audit
snapshot failure, and the two template-service failures. The environment-list-widget SIGSEGV is
the separately recorded flaky/historical member of the same Jira cluster.

### NON-BLOCKER — pre-existing — PYPOST-1262

Jira: [PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262)

- `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::`
  `test_venv_test_installs_when_stamp_stale` (file-level worker timeout; remaining file tests
  have no individual node attribution).
- `tests/test_makefile_targets.py::TestTargetExecution::`
  `test_test_succeeds_from_bare_venv_via_venv_test` (file-level worker timeout; remaining file
  tests have no individual node attribution).

Jira records both workers being killed at the fixed 120-second limit while building and tearing
down real virtual environments under full-suite parallel load. This is an existing test-budget
issue, not a PYPOST-1153 implementation failure.

## Follow-up Tasks

No new Jira issue is created by this Step 7 analysis, per instruction. The only follow-up that
would justify a future Jira ticket is the private pytest parser adapter and compatibility matrix
when the supported pytest/plugin range changes. The remaining items are documented, low-risk
trade-offs or scope limitations and can be addressed opportunistically under test-infrastructure
maintenance.

## Acceptance Assessment

- The seven PYPOST-1153 requirements are represented by implementation and focused tests.
- Every changed test module declares an explicit timeout, and subprocess waits are bounded.
- No new blocker, untracked production change, or duplicate baseline issue was found.
- The implementation is acceptable for the next workflow step, subject to the Step 7 artifact
  review gate.
