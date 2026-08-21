# Roadmap: PYPOST-1064

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `test/PYPOST-1064-source-index-export-precedence`


## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**

  - `ai-tasks/PYPOST-1064/00-roadmap.md` — task progress journal and implementation language recorded.
  - `ai-tasks/PYPOST-1064/10-requirements.md` — business and functional requirements for verifying that target source item takes precedence over distant tree selection during collection export.
- [x] **STEP 2: High-Level Architecture Design**


  - `ai-tasks/PYPOST-1064/20-architecture.md` — test architecture design, module interactions, and Step 3 red repro test strategy for export source_index precedence.
- [x] **STEP 3: Failing Repro Test**

  - `tests/test_collection_export_ui.py::TestExportCollectionSourcePrecedence`
- [x] **STEP 4: Development**

  - [x] Updated `CollectionsPresenter.export_collection` signature to accept `source_index: QModelIndex | None = None` and forward it to `CollectionExportActions.export_collection(source_index=source_index)`.
  - [x] Made the Step 3 red repro test suite in `tests/test_collection_export_ui.py::TestExportCollectionSourcePrecedence` pass (all 19 tests passing).
- [x] **STEP 5: Code Cleanup**


  - `ai-tasks/PYPOST-1064/40-code-cleanup.md` — static analysis (flake8), formatting checks, and type checks verified with zero errors; all tests passing.
- [x] **STEP 6: Observability**


  - `ai-tasks/PYPOST-1064/50-observability.md` — observability requirements analyzed, structured logging documented, safe masking and existing log events verified.
- [x] **STEP 7: Technical Debt Analysis**


  - `ai-tasks/PYPOST-1064/60-tech-debt.md` — technical debt analysis complete; gap from PYPOST-1013 resolved, 0 blockers, all tests passing with explicit timeouts.
- [x] **STEP 8: Dev Docs**


  - `doc/dev/collection_export.md` — documented `CollectionsPresenter.export_collection(source_index=None)` and `CollectionExportActions.export_collection(source_index=None)` precedence over `currentIndex()`, node resolution for collection items and child request items, and integration test coverage.
  - `doc/dev/collection_tree_actions.md` — documented context menu export passing clicked index as `source_index`, node resolution rules, and test references.
- [x] **COMMIT: Commit Changes**


## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1064/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1064/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1064/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1064/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1064/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_export.md`
- `doc/dev/collection_tree_actions.md`

### COMMIT

- Commit: `da095f2a` — `test(export): PYPOST-1064 test source_index overrides distant currentIndex`
