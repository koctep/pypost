# Roadmap: PYPOST-997

## Task Metadata

- **Implementation language**: GitHub Actions YAML / Python / English Markdown
- **Branch name**: feature/PYPOST-997-ci-check-lock-otel

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for adding `check-lock-otel` CI job with pinned uv version to `.github/workflows/test.yml`
  - [x] Produce requirements artifact `ai-tasks/PYPOST-997/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design CI job structure and contract tests in `tests/test_ci_check_lock_job.py`
  - [x] Produce architecture artifact `ai-tasks/PYPOST-997/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `test_workflow_has_otel_check_lock_job` and `test_workflow_check_lock_otel_setup_uv_step_pins_version` in `tests/test_ci_check_lock_job.py`
  - [x] Verified tests failed before editing `test.yml`
- [x] **STEP 4: Development**
  - [x] Added `check-lock-otel` job to `.github/workflows/test.yml` with pinned `version: "0.11.31"`
  - [x] Verified 5/5 tests in `test_ci_check_lock_job.py` pass GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-997/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify CI job summary output
  - [x] Produce `ai-tasks/PYPOST-997/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status
  - [x] Produce `ai-tasks/PYPOST-997/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Verified CI and build documentation
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-997/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-997/20-architecture.md`

### STEP 3: Failing Repro Test
- `tests/test_ci_check_lock_job.py`

### STEP 4: Development
- `.github/workflows/test.yml`
- `tests/test_ci_check_lock_job.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-997/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-997/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-997/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
