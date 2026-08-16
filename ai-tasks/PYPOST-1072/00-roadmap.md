# Roadmap: PYPOST-1072

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `fix/PYPOST-1072-stabilize-migration-worker` (reference only; not switched)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1072/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1072/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Failing repro in `tests/test_settings_encryption_migration_ui.py`:
    `TestSettingsDialogEncryptionMigration::`
    `test_migration_worker_is_retained_until_thread_completion`
- [x] **STEP 4: Development**
  - [x] Split migration domain success from inherited `QThread.finished()` lifecycle cleanup.
  - [x] Retained workers through bounded termination cleanup and restored buttons afterward.
  - [x] Added assertion-producing waits, deterministic lifecycle coverage, and explicit dialog
    teardown.
  - [x] Verified migration and related Qt tests; full suite is green relative to five base failures.
  - [x] Repeated full `make test` twice on the unchanged implementation: run 1 completed in
    549.51 seconds and run 2 in 547.88 seconds pytest / 549.30 seconds wall. Each had 2,205
    passed, 5 failed, and 22 deselected; all migration scenarios completed without hanging, and
    both runs contained only the same five PYPOST-1071 baseline failures.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1072/40-code-cleanup.md`
  - [x] Cleaned scoped import ordering, whitespace, typing, and private-field access.
  - [x] `make lint`, scoped flake8, syntax compilation, and 13 targeted tests passed.
  - [x] Full suite was not repeated after two identical Step 4 runs; the same five PYPOST-1071
    baseline failures remain documented in the cleanup report.
  - [x] `make analyze` is unavailable in the current Makefile; `make typecheck` reports only
    out-of-scope additions over its stored baseline.
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1072/50-observability.md`
  - [x] Audited structured lifecycle logs; no additional production event or metric was needed.
  - [x] Added exact `caplog` coverage for the bounded cleanup timeout warning.
  - [x] Focused worker and settings migration validation passed: 14 tests in 0.23 seconds.
  - [x] Focused flake8, syntax compilation, and diff whitespace validation passed.
- [x] **STEP 7: Technical Debt Analysis**
  - [/] `ai-tasks/PYPOST-1072/60-tech-debt.md`
  - [/] No blocker or timeout-marker gap found; one non-blocking failure-path lifecycle test
    remains as a follow-up.
  - [/] Five exact baseline failures remain `NON-BLOCKER — pre-existing` and deduplicated to
    PYPOST-1071; additional repeated full suites are optional statistical confidence only.
- [x] **STEP 8: Dev Docs**
  - [/] Updated `doc/dev/encryption_key_migration.md` with the split domain-result and native
    thread lifecycle contracts.
  - [/] Documented retained ownership, cleanup ordering, the 100 millisecond warning bound,
    assertion-producing UI waits, validation commands, troubleshooting, and PYPOST-1078.
  - [/] Focused lifecycle validation passed: 14 tests in 0.21 seconds; Markdown link, fence,
    changed-line length, and diff whitespace checks passed.
- [x] **COMMIT: Commit Changes**
  - `fix(ui): PYPOST-1072 stabilize migration worker lifecycle` (see Git history)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1072/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1072/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1072/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1072/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1072/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
