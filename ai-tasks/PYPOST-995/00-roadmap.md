# Roadmap: PYPOST-995

## Task Metadata

- **Implementation language**: Python / YAML
- **Branch name**: feature/PYPOST-995-pin-uv-check-lock-dev

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements to pin uv version on `check-lock-dev` CI job
  - [x] Produce requirements artifact `ai-tasks/PYPOST-995/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design CI workflow version pinning parity across `check-lock` and `check-lock-dev`
  - [x] Produce architecture artifact `ai-tasks/PYPOST-995/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `test_workflow_check_lock_dev_setup_uv_step_pins_version` in `tests/test_ci_check_lock_job.py`
  - [x] Verified test fails before fix
- [x] **STEP 4: Development**
  - [x] Pinned `version: "0.11.31"` on `check-lock-dev` job in `.github/workflows/test.yml`
  - [x] Verified tests pass GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint` and `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-995/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify CI workflow step annotations and test output
  - [x] Produce `ai-tasks/PYPOST-995/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status (check-lock-otel follow-up in PYPOST-997)
  - [x] Produce `ai-tasks/PYPOST-995/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Verify CI and lock testing documentation
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-995/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-995/20-architecture.md`

### STEP 3: Failing Repro Test
- `tests/test_ci_check_lock_job.py`

### STEP 4: Development
- `.github/workflows/test.yml`
- `tests/test_ci_check_lock_job.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-995/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-995/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-995/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
