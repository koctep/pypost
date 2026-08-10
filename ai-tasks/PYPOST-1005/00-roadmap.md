# Roadmap: PYPOST-1005

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import_responsiveness.py`
    (`test_event_loop_stays_responsive_during_collection_import_parse`)
- [x] **STEP 4: Development**
  - [x] Added `CollectionImportParseWorker` (`QThread`) under `pypost/core/qt/`
    to run `read_import_file` off the GUI thread
  - [x] Converted `CollectionImportActions` to `QObject` with async parse →
    sync conflict/plan/apply; busy cue (`is_busy`, Import button disabled,
    status-bar preparing message via injected callables)
  - [x] Wired presenter status-bar show/clear hooks; kept `read_import_file` DI
  - [x] Step 3 responsiveness test green
  - [x] Updated `tests/test_collections_import_ui.py` with `process_until`
    waiters for async parse completion
  - [x] Added `MSG_IMPORT_PREPARING` user-visible string
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-1005/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1005/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1005/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_import_responsiveness.py`
  (event loop + busy cue during import parse; red until Step 4)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1005/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1005/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1005/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md` — async parse worker, busy cue, log events
- `doc/user/collections.md` — preparing cue for large imports
- Cross-ref: `doc/dev/collection_loading.md`

## Suggested branch

`feature/PYPOST-1005-async-collection-import-parse`
