# Roadmap: PYPOST-36

## Task Metadata

- Programming language: Python
- Recommended branch: fix/PYPOST-36-ci-makefile-reliability

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Iteration 1: Updated Makefile to use `.venv`, enforce single-environment execution
    for `run/test/lint`, and align targets to deterministic dependency/bootstrap flow.
  - [x] Iteration 2: Refactored `venv` target to depend on `$(VENV_MARKER)` and moved
    environment initialization to marker target for clearer Make dependency behavior.
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

- `ai-tasks/PYPOST-36/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-36/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-36/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-36/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-36/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
