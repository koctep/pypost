# Roadmap: PYPOST-996

## Task Metadata

- **Implementation language**: Makefile / Python
- **Branch name**: feature/PYPOST-996-makefile-check-lock-retry

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for porting retry/diagnostics/cleanup across all check-lock targets
  - [x] Produce requirements artifact `ai-tasks/PYPOST-996/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design uniform retry, messaging, and scratch file handling for `check-lock`, `check-lock-dev`, and `check-lock-otel`
  - [x] Produce architecture artifact `ai-tasks/PYPOST-996/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Parametrize `tests/test_makefile_check_lock_retry.py` across `("check-lock", "check-lock-dev", "check-lock-otel")`
  - [x] Verify tests fail prior to Makefile update
- [x] **STEP 4: Development**
  - [x] Port 3-attempt retry loop with exponential backoff to `check-lock-dev` and `check-lock-otel` in `Makefile`
  - [x] Port distinct error messages (exhausted retry vs stale lock) to `check-lock-dev` and `check-lock-otel`
  - [x] Ensure scratch file cleanup (`*.check`, `*.body`, `*.check.body`) in all failure and success branches
  - [x] Verify 12/12 tests pass GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Run `make lint` and `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-996/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify Makefile stderr diagnostic outputs for compile retries and stale lock messages
  - [x] Produce `ai-tasks/PYPOST-996/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status
  - [x] Produce `ai-tasks/PYPOST-996/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Check testing and Makefile documentation
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-996/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-996/20-architecture.md`

### STEP 3: Failing Repro Test
- `tests/test_makefile_check_lock_retry.py`

### STEP 4: Development
- `Makefile`
- `tests/test_makefile_check_lock_retry.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-996/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-996/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-996/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
