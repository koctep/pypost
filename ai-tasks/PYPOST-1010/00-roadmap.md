# Roadmap: PYPOST-1010

## Implementation Context

- Programming language: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collection_export_ui.py::TestExportAllCollections::test_all_export_one_collection_writes_object_root`
- [x] **STEP 4: Development**
  - [x] Added a shared JSON root policy and applied it to all-collections export so one
    collection writes an object while zero or multiple collections write arrays.
  - [x] Applied the shared policy at both environment export seams and covered the injected
    environment-widget export path.
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

- `ai-tasks/PYPOST-1010/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1010/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1010/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1010/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1010/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
