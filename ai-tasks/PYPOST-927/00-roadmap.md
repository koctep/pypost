# Roadmap: PYPOST-927

**Programming language:** YAML (GitHub Actions workflow) + Makefile (existing targets)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ci_check_lock_job.py` — fails until `check-lock` job exists
- [x] **STEP 4: Development**
  - [x] Added `check-lock` GitHub Actions job (uv + `make check-lock`)
  - [x] Contract test green
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-927/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-927/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ci_check_lock_job.py`

### STEP 4: Development

- `.github/workflows/test.yml`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-927/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-927/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-927/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/setup.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-927/70-dev-docs.md`
