# Roadmap: PYPOST-805

**Branch (reference):** `chore/PYPOST-805-pip-audit-dev-lock`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pip-audit>=2,<4` to `requirements-dev.in` and `pyproject.toml` dev extra
  - [x] Regenerated `requirements-dev.txt` via `make lock-dev`
  - [x] Removed inline `pip install pip-audit` from Makefile and CI `security-audit` job
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

- `ai-tasks/PYPOST-805/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-805/20-architecture.md`

### STEP 3: Development

- `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml`, `Makefile`, `.github/workflows/test.yml`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-805/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-805/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-805/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/dependencies_audit.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-805/70-dev-docs.md`
