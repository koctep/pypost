# Roadmap: PYPOST-1076

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `documentation/PYPOST-1076-verify-migration-stability`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1076/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1076/20-architecture.md`
  - [x] No distinct production or test change remains; commit `17c20fb9` already provides and
    tests the migration worker lifecycle fix.
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change remains to reproduce: commit `17c20fb9` already separates
    domain success (`succeeded`) from inherited `QThread.finished()` lifecycle completion and
    tests the corrected behavior. Creating a red test against the current tree would manufacture
    a false failure rather than demonstrate an unmet requirement.
  - Existing deterministic lifecycle coverage: `test_reencrypt_runs_when_confirmed` verifies the
    exactly-once confirmed operation and result request;
    `test_migration_worker_is_retained_until_thread_completion` verifies result presentation
    before native completion, retained ownership, deletion, reference release, and restored
    controls.
  - Verification-only next action is the bounded CPython 3.13.13 macOS arm64 validation plan in
    `ai-tasks/PYPOST-1076/20-architecture.md`; no test or production file was changed in Step 3.
- [x] **STEP 4: Development**
  - [x] Verified detached commit `17c20fb9180b05efd16ac04f17dd630efcd16cc1` in a clean,
    throwaway worktree; the four scoped production/test files had no worktree diff.
  - [x] On macOS 15.7.7 arm64, `make PYTHON=<CPython-3.13.13-path> install` exited 0 in
    20.67 seconds. The isolated `.venv/bin/python` reported CPython 3.13.13 and a 64-bit arm64
    Mach-O executable.
  - [x] Focused Makefile validation exited 0: all 14 migration worker and Settings UI tests
    passed in 0.50 seconds (5.68 seconds wall time).
  - [x] Full `make test` run 1 reached 100% with 2,197 passed, 5 failed, 22 deselected, and
    1 warning in 528.34 seconds (531.93 seconds wall time; expected baseline-relative exit 2).
  - [x] Full `make test` run 2 reached 100% with 2,197 passed, 5 failed, 22 deselected, and
    1 warning in 528.27 seconds (529.90 seconds wall time; expected baseline-relative exit 2).
  - [x] Both full runs contained exactly the five documented PYPOST-1071 baseline failures:
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::` +
      `test_audit_module_inventory_within_caps`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::` +
      `test_main_window_class_loc_within_cap`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::` +
      `test_main_window_file_loc_within_cap`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::` +
      `test_markdown_snapshot_matches_current_metrics`
    - `tests/test_verify_ai_task_artifacts.py::TestCommittedBaseline::` +
      `test_baseline_matches_current_scan`
  - [x] Every migration test passed in both full runs; execution continued through the
    remaining suite to its conclusive result with no bus error, fatal interpreter error, hang,
    or process-level termination.
  - [x] Verification changed no production or test file; the throwaway worktree was removed.
- [x] **STEP 5: Code Cleanup**
  - [/] `ai-tasks/PYPOST-1076/40-code-cleanup.md`
  - [/] Verification-only cleanup found no production or test delta against commit `17c20fb9`;
    static analysis and suite results are classified in the cleanup report for gate review.
- [x] **STEP 6: Observability**
  - [/] `ai-tasks/PYPOST-1076/50-observability.md`
  - [/] Verified the existing INFO, WARNING, and ERROR lifecycle event contract from commit
    `17c20fb9`; no production log or metric change is warranted.
  - [/] Recorded affected-platform focused and repeated full-suite evidence plus the required
    diagnostic packet and escalation boundary for any recurring native failure.
- [x] **STEP 7: Technical Debt Analysis**
  - [/] `ai-tasks/PYPOST-1076/60-tech-debt.md`
  - [/] No blocker, timeout-marker omission, or new follow-up was found; PYPOST-1078 remains the
    already-ticketed failure-path coverage follow-up and was not duplicated.
  - [/] Recorded the exact five full-suite failures as **NON-BLOCKER — pre-existing** under
    PYPOST-1071.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/encryption_key_migration.md` with the PYPOST-1076 affected-platform
    verification evidence, reproducible clean-worktree Makefile procedure, baseline exceptions,
    and troubleshooting guidance; no lifecycle design or code/test change was added.
- [x] **COMMIT: Commit Changes**
  - [x] `documentation(test): PYPOST-1076 verify migration stability`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1076/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1076/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1076/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1076/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1076/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
