# Roadmap: PYPOST-929

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile.py` — `TestInstallExtraStampContract` (regression guard; passes on current Makefile)
- [x] **STEP 4: Development**
  - [x] Added `TestInstallExtraStampContract` with stamp existence and skip-pip asserts
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Programming Language

Makefile contract verification via Python pytest (`tests/test_makefile.py`).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-929/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-929/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile.py` — `TestInstallExtraStampContract`

### STEP 4: Development

- `tests/test_makefile.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-929/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-929/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-929/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
