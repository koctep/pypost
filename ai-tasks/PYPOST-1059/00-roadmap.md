# Roadmap: PYPOST-1059

## Task Metadata

- **Implementation language**: Python
- **Branch name**: test/PYPOST-1059-ui-assert-sidebar-matches-disk

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals and motivation
  - [x] Define user stories for sidebar consistency
  - [x] Specify Definition of Done and acceptance criteria
  - [x] Define functional/non-functional scope and Q&A
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research current UI import flow, tree presentation, and test coverage
  - [x] Design failing repro test strategy for Step 3
  - [x] Map UI component interactions and tree model synchronization
  - [x] Draft 20-architecture.md artifact
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collections_import_ui.py` (partial/total save failure UI tree consistency tests and real storage e2e failure test)
- [x] **STEP 4: Development**
  - [x] Implement presenter-level partial save failure test asserting sidebar tree items and model row count match durable storage (`test_partial_save_failure_tree_and_manager_match_durable_storage`)
  - [x] Implement presenter-level total save failure test asserting sidebar tree retains only pre-existing durable collections (`test_total_save_failure_retains_only_preexisting_durable_collections`)
  - [x] Implement end-to-end real storage failure test asserting filesystem state, in-memory collections, and sidebar QTreeView rows strictly match (`test_real_storage_save_failure_reconciles_tree_and_disk`)
  - [x] Verify full regression suites (`tests/test_collections_import_ui.py`, `tests/test_collection_import.py`, `tests/test_collection_import_apply.py`) and static analysis (`make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linting (`make lint`, `make typecheck`, `flake8`)
  - [x] Check formatting, line length <= 100 chars, no dead code or unused imports
  - [x] Verify explicit timeout markers on tests per `do-testing`
  - [x] Create `ai-tasks/PYPOST-1059/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Review structured events emitted during save failures and tree reload (`collection_import_save_failed`, `collection_import_reconciled`, `collection_import_applied`, `collection_import_completed`)
  - [x] Document log reading order and correlation in UI tests and runtime diagnostic traces
  - [x] Validate logging assertions in UI test suite (`tests/test_collections_import_ui.py`, `tests/test_collection_import_apply.py`)
  - [x] Create `ai-tasks/PYPOST-1059/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality, missing tests, performance, and follow-up tasks
  - [x] Verify timeout markers and test suite integrity per `do-testing`
  - [x] Produce `ai-tasks/PYPOST-1059/60-tech-debt.md`
  - [x] Render verdict: SAFE TO CLOSE / BLOCKER analysis
- [x] **STEP 8: Dev Docs**
  - [x] Document UI presenter sidebar tree model synchronization guarantees upon import save failure in `doc/dev/collection_import.md`
  - [x] Document testing guidance and regression test locations for UI storage reconciliation in `doc/dev/collection_import.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1059/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1059/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1059/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1059/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1059/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- `996f2de4` — `test(ui): PYPOST-1059 assert sidebar matches disk after import save failure`
