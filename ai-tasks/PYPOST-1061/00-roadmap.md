# Roadmap: PYPOST-1061

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1061-collection-import-determinate-progress`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1061/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1061/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import_progress.py`
- [x] **STEP 4: Development**
  - [x] Extended `collection_messages.py` with `MSG_IMPORT_VALIDATING` and formatting helper `format_import_validating_message`.
  - [x] Extended `load_collection_import_candidates` with `on_progress` callback parameter invoked per candidate record.
  - [x] Added `parse_progress` / `progress` signal on `CollectionImportParseWorker` with backward-compatible signature inspection.
  - [x] Connected `parse_progress` to status bar formatting in `CollectionImportActions`.
  - [x] Unit, integration, and responsiveness tests passing (58 tests in suite).
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1061/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1061/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1061/60-tech-debt.md`
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

- `ai-tasks/PYPOST-1061/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1061/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1061/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1061/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1061/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit: `c549d848` (`feature(core): PYPOST-1061 determinate progress during collection import validation`)
