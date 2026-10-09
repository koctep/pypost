# PYPOST-1336: Code Cleanup Report

## Linter Fixes

No production code, tests, dependencies, fixtures or configuration changed in this task.
The deliverables are decomposition notes and Jira issues. Existing Python lint passes.

## Code Formatting

- Wrapped the task and epic notes to at most 100 source characters per line.
- Converted the wide architecture module table into equivalent module responsibility bullets.
- Shortened the diagram's resource label; the full file inventory remains in the module notes.
- Soft-wrapped fenced Jira descriptions without changing their acceptance criteria or scope.
- Preserved UTF-8, LF endings and a single final newline; removed trailing whitespace.

## Code Cleanup

Unused imports, unused variables, debug output and dead code are not applicable: this task
changes documentation only. No unrelated code cleanup was performed.

## Validation Results

- `make lint verify-ai-tasks`: PASS after formatting and environment restoration.
- Original `make test`: 381 files; 364 passed, 10 failed, 7 skipped.
- Current focused rerun of the ten affected files: eight pass; target-filtering and
  pytest exit-policy workers time out at 120 seconds.
- Clean baseline rerun: five pass; both stamp modules, target-filtering, target-install
  and pytest exit-policy time out at 120 seconds. Target-install times out after its first
  three tests pass, matching the original run; the refreshed current module passes.
- The missing-runner exit-policy node independently fails at current and base with
  `subprocess.TimeoutExpired` from its nested `make install` after 60 seconds.
- Current collection-export module: all 19 test assertions pass; original and two unchanged
  reruns ended with worker exit -11 after the final assertion. After environment restoration,
  the focused rerun passes with worker exit 0. No test assertion was changed.
- No tests were authored or edited; explicit timeout requirements remain unchanged.
- No source changes require additional syntax or type verification.
- All test processes completed or were cancelled; no test subprocess remains.

## Baseline Triage and Environment Notes

The base commit is `31f2b25a1fcacf490c5136c25ac4dac57ec41b06`. Baseline checks use
an isolated throwaway worktree and its own virtual environment installed through `make install`.
All test invocations use Make targets.

An initial baseline attempt passed an absolute shared `VENV` override to Make. Nested
Makefile tests inherited that override, and their clean target removed the shared environment.
That attempt is invalid and excluded from classification. The pending UI invocation using
that override was cancelled. The root environment was recreated through `make install`;
its editable package points to `/home/src` again. Subsequent checks use separate environments.

The reinstall refreshed allowed dependencies (including PySide6 6.11.1 and pydantic 2.14.0).
The original run and refreshed-environment runs are therefore distinct observations. Both
environments were refreshed through the same Make target; this does not establish identity
with the dependency versions used for the original failure.

Existing follow-ups identified by the orchestrator are PYPOST-1298 (shared Makefile test
fixture locking) and PYPOST-1299 (missing-runner exit-policy hangs). Collection-export worker
crash is tracked by [PYPOST-1357](https://pypost.atlassian.net/browse/PYPOST-1357)
(environment-sensitive crash, 5 SP, outside the sprint and epic). The clean baseline UI module
passes, and two refreshed current UI reruns pass. Step 7 owns follow-up debt recording.

## Triage Classification

- PYPOST-1298: existing Makefile shared-fixture failures; refreshed current fixture setup
  passes, and baseline worker budgets are still exceeded by the stamp and target modules.
  Worker timeouts are process-level failures, not evidence that every assertion failed.
- PYPOST-1299: pre-existing missing-runner exit-policy setup timeout; the standalone current
  and base runs both raise the same exception from `make install`.
- PYPOST-1357: environment-sensitive collection-export worker crash. All 19 assertions pass
  before the original and two unchanged worker crashes; refreshed current runs and base pass.
  Dependency refresh limits the conclusion to an environment-sensitive pre-existing defect.

The original failure log is `/tmp/pypost-sprint-2025-test.log`. Focused current and base logs
are `/tmp/pypost-1336-current-focused.log` and `/tmp/pypost-1336-baseline-clean.log`.
Standalone exit-policy tracebacks are `/tmp/pypost-1336-exit-policy-node.log` and
`/tmp/pypost-1336-exit-policy-baseline-node.log`. The orchestrator receives full node identifiers,
commands and excerpts for Jira follow-up evidence. No unrelated test defect is fixed here.
