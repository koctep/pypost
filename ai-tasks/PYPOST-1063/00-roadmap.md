# Roadmap: PYPOST-1063

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `test/PYPOST-1063-close-async-collection-import-test-gaps`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1063/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1063/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import_async_gaps.py`
- [x] **STEP 4: Development**
  - [x] Implemented and verified test coverage for busy re-entry skip guard (`test_import_skipped_when_already_busy`).
  - [x] Implemented and verified test coverage for unexpected exception handling during parse worker execution (`test_unexpected_reader_exception_surfaces_invalid_dialog`).
  - [x] Implemented and verified test coverage for status bar preparing/clearing lifecycle (`test_status_bar_lifecycle_transitions`).
  - [x] Implemented and verified end-to-end integration test for real multi-record JSON file parsing (`test_real_json_file_async_import_integration`).
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1063/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1063/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1063/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/collection_import.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1063/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1063/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1063/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1063/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1063/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit: `3e528e17` (`test(core): PYPOST-1063 close async collection import test gaps`)
