# Roadmap: PYPOST-989

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red test: `tests/test_collection_export.py` (failed at collection with
        `ModuleNotFoundError: pypost.core.collection_export` before Step 4)
- [x] **STEP 4: Development**
  - [x] `pypost/core/collection_export.py`, `collection_export_actions.py`, UI wiring,
        green tests, `doc/user/collections.md`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-989/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-989/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_export.py`

### STEP 4: Development

- Source code, tests, user docs

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-989/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-989/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-989/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_export.md`, `ai-tasks/PYPOST-989/70-dev-docs.md`

## Suggested branch name (reference only)

`feature/PYPOST-989-export-collection`
