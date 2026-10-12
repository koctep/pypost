# PYPOST-1299: Technical Debt Analysis

## Assessment

The accepted fixture correction satisfies the scoped missing-runner requirements without
changing production Make recipes or increasing deadlines. Both real negative workflows still
assert rejection, diagnostics, root-fragment cleanup, and preservation of base/nested coverage.
No task-caused defect or blocking debt was identified from source inspection and the accepted
Make evidence in the [roadmap](00-roadmap.md). The full gate remains baseline-relative; it is
not wholly green. This analysis does not claim that the repository has no technical debt.

## Shortcuts Taken

None requiring remediation. The local interpreter symlink and Python-version readiness stamps
deliberately represent prerequisites as ready for an early rejection test. They do not establish
a usable installed environment and must not be reused as evidence of successful installation.
This follows the existing local workspace pattern in
`tests/test_parallel_runner_followups_repro.py`; it is the accepted architecture rather than a
temporary workaround. Stamps are created after metadata and initialization to satisfy Make's
timestamp prerequisites. The repro checks those prerequisites before real target delegation.

The fixture relies on existing Make/Unix symlink support and the interpreter running the suite.
It does not add a cross-platform environment implementation or promise tests under an
unavailable interpreter. No newly observed portability gap warrants a speculative follow-up.

## Code Quality Issues

None introduced that require a follow-up. Preparation remains a small local helper; obsolete
package seeding was removed. The subprocess wrapper retains real Make results and checks the
selected target, workspace, missing runner, readiness, and bounded timeout before delegation.
There is no production API or architecture deviation. Version strings, stamp names, and timeout
constants express existing Make contracts and reviewed test budgets, not business configuration.

`make lint` passed in Step 5, but its flake8 target covers production code rather than these
test modules. Manual formatting/import review and accepted test execution cover the changed
tests; no separate test-module static-analysis result is claimed.

## Missing Tests

No blocking gap was found against the accepted requirements. Both original negative checks
execute the copied real Makefile and retain all failure/cleanup assertions. The parameterized
offline repro invokes those original checks and rejects preparation subprocesses, missing/stale
stamps, installation output, extra target invocations, or excessive execution time. It never
synthesizes the Make failure. Adjacent empty-test policies and timeout-budget contracts passed
in the accepted focused run.

All affected original tests retain explicit function timeout markers: 75 seconds for the
negative Make checks and 30 seconds for the empty-test checks. The new repro has a 20-second
module marker, caps delegation at 10 seconds, and asserts elapsed time below 10 seconds.
Original Make subprocesses retain 60-second bounds. No unbounded waits or missing explicit
timeout markers were introduced. Make stderr is asserted directly; this correction adds no
production ERROR logging path requiring a new caplog assertion.

This fixture deliberately bypasses positive dependency installation. Successful installation
and runner execution remain covered by existing separate Make integration checks; the offline
repro alone is not coverage for those paths. No new live network-fault injection, cross-platform
symlink test, or actual coverage-enabled full-suite run is claimed. Those are validation limits,
not missing requirements or newly promised follow-ups.

## Performance Concerns

No unresolved preparation timeout remains in the accepted task checks. Step 4's focused
four-module run completed in 22.84 seconds; the original exit-policy module took 4.29 seconds
and the offline repro 1.30 seconds. The normal eight-worker full gate passed those modules in
8.22 and 2.26 seconds respectively without installation or preparation timeouts. Existing
75-second markers and 60-second original subprocess limits remain intact.

The narrower 10-second repro delegation bound is a regression budget, not a guarantee under a
stalled operating system. Local filesystem responsiveness and process creation remain ordinary
environmental assumptions. There is no new production performance concern to ticket.

## Follow-up Tasks

No new follow-up is required for this implementation. The following five current failures are
**NON-BLOCKER — pre-existing** and already owned by Jira issues. No duplicate issue is needed.
Their baseline proof predates this task: commit `fd830ea8`, in
`/tmp/baseline-PYPOST-1298-step4` with its own relative `.venv`. PYPOST-1299 starts at
`be43fa63`; this step does not claim a fresh baseline run at that commit. Exact historical
baseline commands and failure excerpts are preserved in the predecessor's
[technical-debt evidence](../PYPOST-1298/60-tech-debt.md).

### Flake8 Reporter: PYPOST-1363

[PYPOST-1363](https://pypost.atlassian.net/browse/PYPOST-1363) owns these exact node ids
(join each module and suffix with `::`):

- Module: `tests/test_makefile_exit_behavior.py`.
  Suffix: `TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`.
- Module: `tests/test_makefile_target_filtering.py`.
  Suffix: `TestTargetFiltering::test_lint_succeeds_after_install`.

Both fail with flake8 reporter `KeyError: 'default'` and nested Make lint exit 2.
Baseline log: `/tmp/pypost-1298-step4-baseline-reporter.log`.
Current log: `/tmp/pypost-1299-step4-check.log`. These are not fixture preparation failures.

### Audit Snapshots: PYPOST-1361

[PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361) owns these exact node ids
(join each module and suffix with `::`):

- Module: `tests/test_pypost_1077_verification_artifacts.py`.
  Suffix: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
- Module: `tests/test_pypost_1287_failing_repro.py`.
  Suffix: `test_live_report_inventory_loc_matches_discovery`.
- Module: `tests/test_solid_audit_baseline.py`.
  Suffix: `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`.

Baseline assertions report dialog LOC 1031 versus discovered 1219, a mismatched live inventory
LOC dictionary, and Markdown metrics 459 versus 462. The current run matches those baseline
error classes; this fixture correction changes no audit source or snapshot.
Baseline log: `/tmp/pypost-1298-step4-baseline-other.log`.
Current log: `/tmp/pypost-1299-step4-check.log`.

## Make Verification Evidence

- Focused command (join argument lines with spaces):
  `make test WORKERS=1 PYTEST_ARGS='tests/test_pytest_exit_policy_offline_repro.py
  tests/test_pytest_exit_policy.py tests/test_makefile_parallel_budget.py
  tests/test_parallel_runner_followups_repro.py -q'`.
  All four modules passed; log `/tmp/pypost-1299-step4-focused.log`.
- Normal full gate: `make check`, log `/tmp/pypost-1299-step4-check.log`.
  Root lint passed; tests finished in 249.89 seconds with 393 files, 381 passed,
  five failed, and seven skipped. Only the five tracked failures above remained.
  PYPOST-1338 performance checks passed this run.
- `make verify-ai-tasks` passed separately after the gate stopped at known test failures;
  log `/tmp/pypost-1299-step4-verify.log`. Step 5 `make lint` also passed.

No executable code changed during this analysis, so accepted focused/full verification was
retained without repeating the suite. STEP 7 remains in progress pending independent review
and orchestrator acceptance.
