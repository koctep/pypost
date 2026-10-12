# Roadmap: PYPOST-1298

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Documented timely, trustworthy Make gate feedback under concurrent fixture preparation.
  - Requirements artifact: `ai-tasks/PYPOST-1298/10-requirements.md`.
  - Independent requirements review: PASS; accepted by the orchestrator.
- [x] **STEP 2: High-Level Architecture Design**
  - Designing bounded shared fixture preparation and a deterministic contention repro.
  - Artifact: `ai-tasks/PYPOST-1298/20-architecture.md`.
  - Selected bounded runner pre-dispatch preparation plus helper lock/readiness recovery.
  - Documented 90-second cold preparation and 20-second helper budgets without test changes.
  - Deterministic red repro covers contention, stale cache, stage deadlines, retry, and dispatch.
  - Architecture complete for independent review; STEP 2 remains in progress until acceptance.
  - Reopened for review of measured 21-second materialization budget correction.
  - Revised architecture independent review: PASS; accepted by the orchestrator.
- [x] **STEP 3: Failing Repro Test**
  - Creating offline shared-readiness and runner pre-dispatch regression tests.
  - Added `tests/test_makefile_shared_readiness.py` with an explicit 30-second timeout,
    private shared roots, bounded process/event cleanup, and no external package service.
  - Added runner regressions in `tests/test_run_parallel_tests.py` for normal/coverage
    preparation order, fail-closed behavior, and unrelated/helper-free workspace exclusions.
  - Final focused red command (normal eight-worker runner):
    `make test PYTEST_ARGS='tests/test_makefile_shared_readiness.py
    tests/test_run_parallel_tests.py -k "shared or stale or bootstrap or marker_without
    or materialization or parallel_consumers or make_fixture" --tb=short'`.
    Command arguments above form one line; output captured in `/tmp/pypost-1298-step3-red.log`.
  - Result: Make exit 2; helper regressions 7 failed / 1 passed; runner regressions
    4 failed / 2 passed. All failures assert missing desired behavior on current APIs;
    no production/helper implementation changed, no skipped/xfail tests, and no test timeouts.
  - In `tests/test_makefile_shared_readiness.py`,
    `test_lock_contention_expires_without_blocking_operation`
    rejects current `LOCK_EX`: `RuntimeError: unbounded blocking flock attempted`, which
    fails the expected stage-specific deadline exception assertion immediately.
  - `tests/test_makefile_shared_readiness.py::test_stale_process_cache_requires_published_readiness`
    fails `AssertionError: incomplete cached directory was returned`; marker-only cache,
    cumulative bootstrap deadlines, timeout/nonzero recovery, and partial copy retry also fail.
  - In `tests/test_run_parallel_tests.py`,
    `test_make_fixture_preparation_precedes_dispatch_and_fails_closed`
    fails all four normal/coverage and success/failure cases: success events contain only
    `['dispatch']`; simulated prerequisite failure still reports success and dispatches a unit.
  - Three independent consumers successfully wait for one builder and receive distinct ready
    workspaces; a returned interpreter executes an offline sanity check. Both exclusion cases pass.
  - Early run exposed a coverage mock method typo; corrected the test harness and re-ran before
    recording the final red evidence. STEP 3 remains `[/]` pending independent review.
- [x] **STEP 4: Development**
  - Added bounded prerequisite process-group termination and readiness predicates.
  - Replaced blocking flock with nonblocking polls under one monotonic preparation deadline;
    validate interpreter and pytest/flake8 imports before publishing readiness, reset stale cache,
    and clean incomplete preparation only while owning the lock.
  - Added conditional runner preparation before worker dispatch (90-second preparation budget,
    95-second watchdog), fail-closed summary/report, and bounded partial-copy recovery.
  - Regression mocks now patch bounded Popen command wrappers instead of subprocess.run;
    preserved behavioral assertions and all existing timeout markers.
  - Focused command `make test PYTEST_ARGS='tests/test_makefile_shared_readiness.py
    tests/test_run_parallel_tests.py --tb=short'` passed both files (8 helper and 58 runner tests).
    Arguments form one line; log: `/tmp/pypost-1298-step4-focused.log`.
  - Original five-second copy bound failed serial and eight-worker Make fixture trials;
    recursive hardlinks without metadata preservation also failed. Retained archive hardlinks
    and corrected the architecture to a 15-second total copy bound (14 command + one cleanup).
    Existing test deadlines are unchanged; logs: `/tmp/pypost-1298-step4-copy-serial.log`,
    `/tmp/pypost-1298-step4-copy-recursive.log`, `/tmp/pypost-1298-step4-copy-14s.log`.
  - Affected 14 Make fixture files at normal eight workers: 11 passed, one excluded by the
    existing slow filter, two flake8 reporter failures; no preparation or materialization
    timeouts. Log: `/tmp/pypost-1298-step4-affected-15s.log`.
  - Added real offline helper/runner descendant-termination regressions and unrelated lock
    error propagation coverage; lock polls only EACCES/EAGAIN.
  - Running normal `make check`; log: `/tmp/pypost-1298-step4-check.log`.
  - Final focused rerun passed 11 helper and 60 runner tests, including real descendants,
    nonzero runner preparation and unrelated lock errors; log:
    `/tmp/pypost-1298-step4-focused-final.log`.
  - First full `make check` passed lint; its normal 392-file test run had 376 passed,
    nine failed, seven filtered. Copy timeouts overlapped an isolated baseline dependency
    installation; rerunning the unchanged gate without that competing installation.
  - Separate `make verify-ai-tasks` passed; log: `/tmp/pypost-1298-step4-verify.log`.
  - Baseline `fd830ea8` in `/tmp/baseline-PYPOST-1298-step4` with its own relative `.venv`
    reproduces both flake8 reporter failures with `KeyError: 'default'`:
    `tests/test_makefile_exit_behavior.py::TestExitBehavior::`
    `test_lint_succeeds_from_bare_venv_via_venv_test` and
    `tests/test_makefile_target_filtering.py::TestTargetFiltering::`
    `test_lint_succeeds_after_install` (node-id fragments join without whitespace).
    Exact Make command and failure output: `/tmp/pypost-1298-step4-baseline-reporter.log`.
  - The same baseline reproduces all three audit snapshot assertions and the
    `tests/test_pytest_exit_policy.py` worker watchdog (120 seconds):
    `tests/test_pypost_1077_verification_artifacts.py::`
    `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`,
    `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery`,
    `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::`
    `test_markdown_snapshot_matches_current_metrics` (fragments join without whitespace).
    Baseline log: `/tmp/pypost-1298-step4-baseline-other.log`.
  - Unchanged full gate without baseline workload still exceeded the 14-second command
    deadline in the Otel stamp and recipe-help class fixtures; log:
    `/tmp/pypost-1298-step4-check-final.log`. Corrected the architecture and implementation
    to a 21-second total materialization bound (20 command + one cleanup), preserving all
    existing test deadlines and nine seconds for the shortest recipe-test work.
  - Running normal full `make check` with that corrected bound; log:
    `/tmp/pypost-1298-step4-check-21s.log`.
  - Final normal `make check` with the corrected bound: lint passed; 392 test files,
    378 passed, seven failed, seven filtered; zero shared preparation or copy timeouts.
    All 11 readiness and 60 runner regressions passed, as did every affected Make fixture
    file except the two baseline-proven flake8 reporter failures.
  - Final `make verify-ai-tasks` passed after the full gate's baseline-relative test failure;
    log: `/tmp/pypost-1298-step4-verify-final.log`.
  - Performance node `tests/test_collection_import_profile.py::`
    `test_plan_collection_import_large_dataset_performance` (fragments join) was flaky:
    first full gate passed; later full gates failed at 108.83/138.11 ms versus 100 ms;
    unchanged-tree exact-node rerun passed, and baseline exact-node rerun passed.
    Logs: `/tmp/pypost-1298-step4-performance-rerun.log`,
    `/tmp/pypost-1298-step4-baseline-precise.log`. Verdict: NON-BLOCKER, flaky.
  - Exact baseline exit-policy node `tests/test_pytest_exit_policy.py::`
    `test_make_test_fails_closed_when_parallel_runner_is_missing` reproduced
    `subprocess.TimeoutExpired` from its fixture's `make install` after 60 seconds.
    Baseline precise log captures that complete traceback, in addition to the same
    baseline/current 120-second module watchdog. Verdict: NON-BLOCKER, pre-existing.
  - Step 4 implementation and verification complete for independent acceptance; left `[/]`.
  - Review correction: terminate the runner preparation process group before raising on
    nonzero exit, including descendants whose standard streams are redirected. The helper
    already performs this cleanup; its behavior is covered alongside the runner.
  - Expanded the real offline descendant regression to timeout and nonzero-exit cases.
    Before correction, only
    `tests/test_makefile_shared_readiness.py::test_preparation_failure_terminates_descendants`
    `[True-True]` failed (node-id fragments join); three other cases passed. Red log:
    `/tmp/pypost-1298-step4-cleanup-red.log`.
  - Corrected focused `make test` passed all 13 readiness and 60 runner tests, retaining
    fail-closed preparation assertions; `make lint` passed. Logs:
    `/tmp/pypost-1298-step4-cleanup-focused.log`, `/tmp/pypost-1298-step4-cleanup-lint.log`.
    Existing deadlines are unchanged; STEP 4 remains `[/]` pending independent acceptance.
- [x] **STEP 5: Code Cleanup**
  - Checking scoped formatting, imports, timeout markers, and Make lint evidence.
  - Status correction: STEP 2, STEP 3, and STEP 4 have passed independent review and were
    accepted by the orchestrator. Earlier in-progress/running notes above are historical.
  - Wrapped one 101-character readiness-test line; no behavioral changes or deadline changes.
  - Standard `make lint` passed; supplemental Make scoped flake8 passed with inherited
    runner E203/T201 diagnostics baseline-confirmed and excluded from the scoped runner check.
  - Supplemental Make checks passed syntax, 100-column formatting, whitespace, final
    newlines, conflict markers, and both changed test modules' explicit timeout declarations.
  - Focused `make test` rerun passed both files (13 readiness and 60 runner cases), 18.22 s;
    log: `/tmp/pypost-1298-step5-focused.log`. Full gate evidence remains baseline-relative
    as recorded above; no full-suite repeat for this formatting-only change.
  - Artifact: `ai-tasks/PYPOST-1298/40-code-cleanup.md`; STEP 5 left `[/]` for review.
- [x] **STEP 6: Observability**
  - Inspecting existing bounded helper diagnostics and runner structured failure summaries.
  - Documented existing stage/path/budget errors, failed preparation summaries, JSON reports,
    and scalar validation/completion events in `ai-tasks/PYPOST-1298/50-observability.md`.
  - No missing necessary logging found; application monitoring metrics are N/A for test
    infrastructure. No implementation or test changes; reused Step 5's 73 passing cases.
  - Source inspection confirms preparation failure emits correlated failure/completion events
    and schedules zero workers. STEP 6 remains `[/]` for independent acceptance.
  - Step 6 documentation validation: `make lint` passed, including Markdown and relative links.
- [x] **STEP 7: Technical Debt Analysis**
  - Reviewing accepted readiness/runner behavior against requirements, architecture, and tests.
  - Artifact: `ai-tasks/PYPOST-1298/60-tech-debt.md`; no new blocking debt or concrete
    implementation follow-up identified. Recorded reviewed budget correction and test limits.
  - Preserved all seven baseline-relative failure nodes, exact historical Make commands,
    `fd830ea8` evidence/logs, and existing PYPOST-1363/1361/1299/1338 Jira browse links.
  - Reused 73 focused passes and final normal full-gate evidence (378 passed, seven failed,
    seven filtered, zero shared preparation/copy timeouts). No code or test edits in this step.
  - Step 7 `make lint` passed, including Markdown lint and relative documentation links.
  - STEP 7 left `[/]` for independent review and orchestrator acceptance.
- [x] **STEP 8: Dev Docs**
  - Updating `doc/dev/testing.md` shared Make fixture preparation and troubleshooting reference.
  - Documented pre-dispatch selection/order, cumulative preparation and copy budgets,
    readiness/cache recovery, process-group cleanup, retry, and stage-specific troubleshooting.
  - Replaced obsolete blocking-lock and guaranteed timing claims; retained unchanged test
    deadlines and worker settings. Added focused Make-only usage commands.
  - `make lint` passed; its documentation checks cover 17 user-guide and 19 link-scope files,
    so the developer reference update was also checked directly against helper/runner behavior.
  - No code or test edits; STEP 8 remains `[/]` for independent review and acceptance.
  - Review correction: qualified the older PYPOST-1262 operational note to describe caching
    as reducing repeated setup work, without guaranteeing completion under contention.
    Linked the note to PYPOST-1298 bounded preparation/materialization; STEP 8 remains `[/]`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1298/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1298/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1298/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1298/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1298/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
