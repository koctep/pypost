# Roadmap: PYPOST-779

**Branch (reference):** `chore/PYPOST-779-commit-lock-file`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `requirements.in` as direct-dependency source of truth
  - [x] Compiled transitive `requirements.txt` lock via `uv pip compile` (Python 3.11)
  - [x] Added `make lock` and `make check-lock` Makefile targets
  - [x] Updated CI pip cache paths and developer documentation
  - [x] Added Makefile lock-file tests in `tests/test_makefile.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.11+ (lock compiled for 3.11; CI matrix 3.11 and 3.13)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-779/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-779/20-architecture.md`

### STEP 3: Development

- `requirements.in`, `requirements.txt`
- `Makefile`, `.github/workflows/test.yml`
- `tests/test_makefile.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-779/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-779/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-779/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/dependencies_audit.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-779/70-dev-docs.md`
