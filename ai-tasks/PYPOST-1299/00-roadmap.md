# Roadmap: PYPOST-1299

## Task Metadata

- **Implementation language**: Python; existing Make workflows remain the verification interface.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Recorded timely missing-runner failure and coverage preservation outcomes.
  - Confirmed baseline evidence reports a preparation timeout before the intended failure check.
- [x] **STEP 2: High-Level Architecture Design**
  - `20-architecture.md`: local interpreter/stamp fixture; existing Make guards remain intact.
  - Designed deterministic offline red repro for both real negative checks before helper changes.
  - Preserved timeout-budget contracts; architecture awaits independent acceptance.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pytest_exit_policy_offline_repro.py`: execute both original negative checks;
    reject preparation subprocesses before delegation to real Make targets.
  - Red verification: `make test WORKERS=1 PYTEST_ARGS='tests/test_pytest_exit_policy_offline_repro.py -q'`
    returned exit 2; both parameter cases failed immediately at the existing `make install`
    call with `missing-runner preparation must be offline; unexpected preparation subprocess`.
    Cases took 24 ms and 37 ms; pytest finished in 0.27 seconds, without installation delegation.
  - Real target delegation retains original diagnostic, failure, and scoped coverage assertions;
    prerequisite checks prevent accidental bootstrap, with explicit 20-second test timeout and
    10-second subprocess bound. Original negative fixture remains unchanged pending Step 4.
- [x] **STEP 4: Development**
  - Implementing the approved offline preparation fixture after accepted red repro.
  - [x] Replaced missing-runner `make install` with the current interpreter symlink and
    initialized/test/OTel stamps written after metadata; removed obsolete package seeding.
    Actual Make targets, failure/coverage assertions, 75-second markers, and 60-second
    subprocess bounds remain unchanged. No production Makefile change was necessary.
  - Red reconfirmation before the change: both offline cases failed at forbidden installation;
    log `/tmp/pypost-1299-step4-before.log`.
  - Focused verification passed all four modules in 22.84 seconds:
    `make test WORKERS=1 PYTEST_ARGS='tests/test_pytest_exit_policy_offline_repro.py
    tests/test_pytest_exit_policy.py tests/test_makefile_parallel_budget.py
    tests/test_parallel_runner_followups_repro.py -q'` (join argument lines with spaces).
    Log `/tmp/pypost-1299-step4-focused.log`; original exit-policy module 4.29 seconds,
    offline repro 1.30 seconds, timeout-budget contract and adjacent follow-ups passed.
  - Normal `make check` completed testing in 249.89 seconds: 393 files, 381 passed,
    5 failed, 7 skipped. Root static/doc lint passed. Original exit-policy module passed
    in 8.22 seconds and offline repro in 2.26 seconds under ordinary eight-worker load.
    Log `/tmp/pypost-1299-step4-check.log`.
  - The five remaining failures match previously evidenced, tracked baseline clusters:
    PYPOST-1363 reporter `KeyError: 'default'` (two nodes) and PYPOST-1361 audit snapshot
    drift (three nodes). No additional failure or preparation timeout occurred; PYPOST-1338
    performance checks passed this run. Baseline evidence and exact nodes are recorded in
    `../PYPOST-1298/60-tech-debt.md`; current assertions match those baseline errors.
  - `make verify-ai-tasks` passed separately after `make check` stopped at known test failures;
    log `/tmp/pypost-1299-step4-verify.log`. Awaiting independent Step 4 review.
- [x] **STEP 5: Code Cleanup**
  - Reviewing fixture/repro formatting, imports, bounded waits, and explicit timeouts.
  - `40-code-cleanup.md`: no additional code cleanup required; changed lines satisfy
    100-column formatting and all touched tests retain explicit, bounded timeouts.
  - `make lint` passed (production flake8 and existing user-doc lint/link checks).
    Accepted Step 4 test evidence retained without repeat because code was unchanged;
    full-suite five tracked baseline failures remain documented. Awaiting Step 5 review.
- [x] **STEP 6: Observability**
  - `50-observability.md`: retained real Make stderr diagnostic and nonzero-exit/coverage
    assertions; offline repro identifies unexpected preparation and missing/stale stamps.
  - Production metrics and additional logging are N/A for this isolated fixture correction.
    Accepted Step 4 focused/full test evidence and Step 5 lint evidence retained; no
    executable change in this step. Awaiting independent Step 6 review.
- [x] **STEP 7: Technical Debt Analysis**
  - Assessing accepted fixture/repro constraints and known baseline failure ownership.
  - `60-tech-debt.md`: no task-caused blocker or new follow-up; recorded early-rejection
    stamp/interpreter assumptions, explicit timeout coverage, and positive-installation
    validation limits. Five current full-gate failures remain NON-BLOCKER, pre-existing,
    owned by PYPOST-1363 and PYPOST-1361 with exact node components and baseline/current logs.
  - Accepted Step 4 focused/full and Step 5 lint evidence retained; no executable change or
    duplicate Jira issue. Awaiting independent Step 7 review.
- [x] **STEP 8: Dev Docs**
  - Updating `doc/dev/testing.md` with offline missing-runner fixture preparation,
    unchanged real Make failure/coverage checks, timeout budgets, and troubleshooting.
  - `doc/dev/testing.md`: added one concise Makefile automation subsection describing
    local interpreter/stamp ordering, early rejection and scoped coverage cleanup, original
    75/60-second limits, offline repro bounds, Make usage, and stale-stamp troubleshooting.
  - `make lint` passed (production flake8, 17-file doc lint, 19-file relative-link checks).
    Accepted Step 4 test evidence retained; no executable change or broad test repeat.
    Awaiting independent Step 8 review.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1299/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1299/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1299/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1299/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1299/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
