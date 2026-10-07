# PYPOST-1266: Code Cleanup Report

## Cleanup Review

- Reviewed the worker protocol/direct invocation, presenter injection type, migrated reader
  fakes, and focused reader-contract tests against the accepted architecture.
- No additional formatting, import, dead-code, or debug-output changes were needed.
- Changed test modules declare explicit timeout markers; new worker tests use bounded waits
  and interruption cleanup. Existing script-string fixtures are intentional test data.
- No merge-conflict markers were found in the changed source and test files.
- Refreshed the SOLID metrics snapshot with `make baseline-metrics`; the only change is the
  presenter line count, 522 to 520, caused by the shorter injection type annotation.

## Validation Results

- Full `make check WORKER_TIMEOUT=120` ran once with the default fast-suite selection and no
  added test exclusions. It exited 2: 372 files, 359 passed, 7 failed, 6 skipped, 315.16 seconds.
  Production lint and documentation/link checks passed. Reader-contract, progress,
  responsiveness, and collection UI modules passed in this run.
- `make verify-ai-tasks` passed separately after the failed test gate: 391 completed tasks,
  two grandfathered legacy gaps.
- After the snapshot correction, `make test PYTEST_ARGS=tests/test_solid_audit_baseline.py
  WORKERS=1 WORKER_TIMEOUT=120` passed. The unchanged full suite was not rerun.
- Step 4's `make typecheck` passed against the unchanged 181-error baseline. No Python edits
  were made in Step 5, so the typecheck and focused tests were not repeated.
- The repository has no `make analyze` target; `make check` runs its existing `make lint` gate.
- The lint target checks `pypost/`, not tests; this existing coverage gap is PYPOST-1303.

## Full-Suite Failure Evidence

The complete output is `/tmp/p1266-step5-check.log`, run ID `b5bf38645a93`.

- `tests/test_environment_export_ui.py`: exit -11 after all eight collected tests reported
  PASSED, ending with `TestExportEnvironments::test_logs_completed_event`. No crash traceback
  was emitted; cause and baseline status are unproven.
- `tests/test_makefile_recipes.py`: exit 1, 18 passed and 18 setup errors in
  `TestDependencyChain`. First ID: `test_install_depends_on_marker_only`. The shared stack is
  `makefile_test_helpers.py:425` to `_materialize_prewarmed_venv` at line 409, then
  `subprocess.run`: `Failed: Timeout (>30.0s) from pytest-timeout.` Baseline status is unproven.
- `tests/test_makefile_install_stamp_contract.py`: exit 1. Failing ID:
  `TestInstallExtraStampContract::test_install_touches_both_extra_stamps`; line 39 calls
  `_run_make(make_workspace, "install")`, then `makefile_test_helpers.py:83`:
  `Failed: Timeout (>60.0s) from pytest-timeout.` Baseline status is unproven.
- `tests/test_makefile_stamp_test_idempotency.py`: exit 1. Failing ID:
  `TestVenvTestStampIdempotency::test_venv_test_skips_pip_when_current`; line 34 calls
  `_run_make(make_workspace, "venv-test")`, then `makefile_test_helpers.py:83`:
  `Failed: Timeout (>60.0s) from pytest-timeout.` Baseline status is unproven.
- `tests/test_makefile_target_filtering.py`: exit -9, `worker timeout after 120.0s`.
  `TestTargetFiltering::test_make_test_excludes_slow_marker` reported FAILED without its
  traceback before termination. Two later tests passed; termination occurred during
  `TestTargetFiltering::test_lint_succeeds_after_install`. Baseline status is unproven.
- `tests/test_solid_audit_baseline.py`: exit 1. Failing ID:
  `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`; assertion showed
  stored `522 | 535` versus current `520 | 535`. This task-caused snapshot drift is corrected
  and the focused module now passes; cap checks also passed in the original full run.
- `tests/test_pytest_exit_policy.py`: exit -9, `worker timeout after 120.0s`.
  `test_make_test_fails_closed_when_parallel_runner_is_missing` reported FAILED at 60.05 seconds;
  termination occurred during `test_make_test_cov_fails_closed_when_parallel_runner_is_missing`.
  The orchestrator identified this existing timeout as PYPOST-1299 before this run.

## Resumed Failure Triage

The task base is `280840914e2d4109ce363fbbf64c027efd1d0999` (`28084091`). A fresh detached
worktree was created at `/tmp/baseline-PYPOST-1266-resume`; the partial, unregistered directory
`/tmp/baseline-PYPOST-1266` was not reused. Baseline production and tests had no diff.

The baseline reused `/home/src/.venv` through a worktree-local symlink. Make's
`-o pyproject.toml` prevented dependency stamp refreshes and editable installs in that shared
environment. The parallel runner prepends its checkout root to worker `PYTHONPATH`, and the
baseline pytest output confirms its root directory is the baseline checkout. No command-line
`VENV` override was used, because nested Make tests would inherit it.

All commands below ran through Make. Shell line continuations only wrap the executed arguments.

### Baseline Run

Working directory: `/tmp/baseline-PYPOST-1266-resume`.

```bash
make -o pyproject.toml test \
  PYTEST_ARGS='tests/test_environment_export_ui.py '\
'tests/test_makefile_recipes.py '\
'tests/test_makefile_install_stamp_contract.py '\
'tests/test_makefile_stamp_test_idempotency.py '\
'tests/test_makefile_target_filtering.py '\
'tests/test_pytest_exit_policy.py' \
  WORKERS=4 WORKER_TIMEOUT=120
```

Log: `/tmp/p1266-step5-baseline-resume.log`; run ID `a1e3573d2213`; exit 2. Six modules:
five passed, one failed, 150.23 seconds wall time.

| Module | Baseline outcome | Duration |
| --- | --- | --- |
| `test_environment_export_ui.py` | PASS | 3.57 s |
| `test_makefile_recipes.py` | PASS | 30.16 s |
| `test_makefile_install_stamp_contract.py` | PASS | 55.87 s |
| `test_makefile_stamp_test_idempotency.py` | PASS | 70.61 s |
| `test_makefile_target_filtering.py` | PASS | 82.91 s |
| `test_pytest_exit_policy.py` | TIMEOUT | 120.05 s |

The exit-policy failure repeats the original run's error at this task's base:

```text
tests/test_pytest_exit_policy.py::
test_make_test_fails_closed_when_parallel_runner_is_missing FAILED [60.07s]
tests/test_pytest_exit_policy.py::
test_make_test_cov_fails_closed_when_parallel_runner_is_missing
worker timeout after 120.0s
exit_code=-9
```

The two lines in each identifier above concatenate without whitespace. Verdict:
`NON-BLOCKER — pre-existing`; already tracked by
[PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299). This also corroborates the
earlier `10ba60b7` baseline evidence recorded in PYPOST-1286's cleanup report.

### Export UI Flake

Working directory: `/home/src`. This exact command ran twice against unchanged production
and tests:

```bash
make test PYTEST_ARGS=tests/test_environment_export_ui.py WORKERS=1 WORKER_TIMEOUT=120
```

- Rerun 1: exit 0, one module passed, 1.58 seconds; run ID `0975f6e254bb`;
  log `/tmp/p1266-step5-ui-rerun-1.log`.
- Rerun 2: exit 0, one module passed, 1.57 seconds; run ID `e75c75f1bda6`;
  log `/tmp/p1266-step5-ui-rerun-2.log`.
- Original full check: all eight test bodies passed, followed by worker exit -11. The last
  completed node was `tests/test_environment_export_ui.py::TestExportEnvironments::` plus
  `test_logs_completed_event`; no crash traceback was emitted.
- Current-tree observations: one failed module run and two passing module runs. The baseline
  pass is a separate observation. This does not establish a crash probability.

Verdict: `NON-BLOCKER — pre-existing (flaky)` under the unchanged-tree rerun rule. Root cause
is not investigated. The orchestrator deduplicated, created, and verified
[PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315), with all eight full test IDs,
the failure excerpt, exact commands, and baseline evidence.

### Makefile Timeout Clusters

The four modules passed at this task's base. Existing
[PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298) covers these same modules and
their shared-venv setup, copy, and Make subprocess timeouts. Its earlier evidence includes
`10ba60b7` baseline failures and two passing unchanged-tree reruns.

Working directory: `/home/src`. The following command ran twice against unchanged production
and tests, selecting the four originally failing modules without exclusions or test changes:

```bash
make test \
  PYTEST_ARGS='tests/test_makefile_recipes.py '\
'tests/test_makefile_install_stamp_contract.py '\
'tests/test_makefile_stamp_test_idempotency.py '\
'tests/test_makefile_target_filtering.py' \
  WORKERS=4 WORKER_TIMEOUT=120
```

| Module | Rerun 1 | Rerun 2 |
| --- | --- | --- |
| `test_makefile_recipes.py` | PASS, 25.72 s | PASS, 25.40 s |
| `test_makefile_install_stamp_contract.py` | PASS, 47.55 s | PASS, 48.45 s |
| `test_makefile_stamp_test_idempotency.py` | PASS, 59.34 s | PASS, 60.38 s |
| `test_makefile_target_filtering.py` | PASS, 72.83 s | PASS, 74.28 s |

- Rerun 1: exit 0, four modules passed, 72.84 seconds wall time;
  run ID `b8b735a64691`; log `/tmp/p1266-step5-make-rerun-1.log`.
- Rerun 2: exit 0, four modules passed, 74.29 seconds wall time;
  run ID `193615d41139`; log `/tmp/p1266-step5-make-rerun-2.log`.
- For each module, current-tree observations are one failed and two passing module runs.
  Their baseline passes are separate observations. This does not estimate failure probability.

Verdict for all four: `NON-BLOCKER — pre-existing (flaky)`, deduplicated to PYPOST-1298.
The original recipe fixture error occurred while copying the shared virtual environment;
the install and stamp failures occurred while waiting for nested Make subprocesses. Shared
environment contention or setup cost is suspected, but this run does not prove a common lock
root cause for every timeout. Exact affected identifiers are recorded in the preliminary
[technical debt record](60-tech-debt.md); original excerpts remain above and in the full log.

### Triage Completion

The fresh baseline worktree was removed after its run. The original partial baseline
directory was left untouched. Root environment initialization and dependency stamp timestamps
remained unchanged. No whole-suite rerun, production edit, test edit, skip, or xfail was added.

All six remaining full-check failures are now classified and linked to Jira. The snapshot
regression caused by this task was already corrected and its focused test passed. There is no
unclassified or caused-by-this-task failure remaining in the recorded full check.

`make lint-docs verify-ai-tasks` passed after the triage updates; log:
`/tmp/p1266-step5-triage-artifacts.log`. The existing documentation checks cover 16 user-guide
files and 18 link-check files; the artifact gate reports 391 completed tasks and two
grandfathered legacy gaps. Its existing scope does not validate Markdown style in this open
task's reports.

## Acceptance

Step 5 remains `[/]` for the acceptance gate owner. The task-caused snapshot drift is fixed,
and all six remaining failures are documented, filed non-blockers. Independent review and
acceptance remain the orchestrator's responsibility.
