# Roadmap: PYPOST-780

**Branch (reference):** `chore/PYPOST-780-consolidate-dev-dependencies`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `requirements-dev.in` and compiled `requirements-dev.txt`
  - [x] Updated Makefile `venv-test`, `lock-dev`, `check-lock-dev`
  - [x] Updated CI to install from `requirements-dev.txt`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-780/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-780/20-architecture.md`

### STEP 3: Development

- `requirements-dev.in`, `requirements-dev.txt`
- `Makefile`, `.github/workflows/test.yml`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-780/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-780/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-780/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/dependencies_audit.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-780/70-dev-docs.md`
