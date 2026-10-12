# PYPOST-1299: Timely verification of missing parallel runner failures

## Goals

Give maintainers trustworthy, timely feedback when required test execution support is missing.
Negative checks must reach the intended failure condition without spending their time budget on
unnecessary preparation. This restores useful feedback from the repository quality gate while
preserving confidence in failure reporting and coverage data protection.

## User Stories

- As a maintainer, I can run the missing-runner checks and receive their actual result before
  the configured check and worker deadlines.
- As a maintainer, I can trust that a missing required runner causes test workflows to fail
  clearly instead of appearing successful.
- As a maintainer, I retain persistent and unrelated coverage data when a failed run removes
  disposable coverage fragments.

## Definition of Done

1. Both ordinary and coverage-enabled missing-runner checks complete within their configured
   deadlines during focused execution and the full quality gate, without preparation timeouts.
2. Each check exercises the real workflow with the required runner absent and verifies a
   nonzero result with an explicit missing-runner diagnostic.
3. Both workflows remove disposable root coverage fragments on that failure while preserving
   the root base coverage file and nested coverage fragments.
4. Preparation for this negative scenario does not install unnecessary dependencies or require
   network availability.
5. The checks retain bounded execution and detect regressions in the failure and cleanup
   outcomes rather than accepting an unrelated preparation failure as success.
6. Existing successful test execution and empty-test policy behavior remain supported.

## Task Description

The affected checks are in `tests/test_pytest_exit_policy.py`:

- `test_make_test_fails_closed_when_parallel_runner_is_missing`
- `test_make_test_cov_fails_closed_when_parallel_runner_is_missing`

They currently can exhaust their execution budgets before observing the intended missing-runner
behavior. Supplied baseline evidence specifically shows temporary-project preparation timing
out after 60 seconds. That evidence does not establish a defect in the workflow's missing-runner
guard itself. The scope is reliable verification of the existing rejection and coverage cleanup
contract; broader dependency management and runner redesign are outside this issue.

### Implementation Language

Python. Existing Make workflows are the required interface for repository verification.

### Functional Requirements

- Verify rejection of a missing required runner for ordinary and coverage-enabled test runs.
- Verify the missing-runner diagnostic, failure result, and scoped cleanup together.
- Preserve unrelated coverage artifacts and the existing empty-test policy checks.

### Non-Functional Requirements

- Complete comfortably before existing execution deadlines without increasing those deadlines
  to conceal preparation delays.
- Remain reproducible without external package downloads for this negative scenario.
- Keep all verification bounded and routed through Make targets.

### Scope, Constraints, and Assumptions

- Limit changes to the affected negative scenario and directly necessary supporting behavior.
- Preserve actual workflow execution in the checks; simulated success cannot satisfy the task.
- The supplied evidence reproduces the failure before the preceding shared-preparation change.
- No production messaging feature or public product interface change is required.
- Full-suite results must distinguish this issue's failures from unrelated baseline failures.

### Business Entities and Interactions

- Maintainer: requests a quality check and needs timely, actionable results.
- Test workflow: ordinary or coverage-enabled execution, with a failure status and diagnostic.
- Required runner: available or missing; absence must prevent successful test execution.
- Coverage artifact: disposable root fragment, persistent base data, or unrelated nested data.
  A rejected test workflow removes only the disposable root fragments.

## Q&A

- Why is this work needed? Preparation timeouts hide the intended failure result and slow the
  quality gate, reducing maintainers' confidence in negative checks.
- Is the missing-runner guard proven defective? No. Supplied evidence shows preparation timing
  out first; investigation must preserve that distinction.
- What evidence defines the problem? The supplied baseline log
  `/tmp/pypost-1298-step4-baseline-precise.log` records a 60-second preparation timeout for the
  ordinary missing-runner check. The issue also reports the coverage-enabled check timing out.
- Are longer deadlines acceptable as the fix? No. The required outcome is timely, meaningful
  verification without unnecessary installation for the negative scenario.
