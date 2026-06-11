# Roadmap: PYPOST-317

- Programming language: Python
- Recommended branch: test/PYPOST-317-save-as-orchestrator-tests

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Iteration 1: Added orchestrator-level save-as tests with mocked `SaveRequestDialog` in
    `tests/test_request_save_orchestrator.py` (happy path, cancel paths, new collection,
    collection expand, source immutability).
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

- `ai-tasks/PYPOST-317/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-317/20-architecture.md`

### STEP 3: Development

- `tests/test_request_save_orchestrator.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-317/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-317/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-317/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-317/70-dev-docs.md`
- `doc/dev/request_actions.md`
