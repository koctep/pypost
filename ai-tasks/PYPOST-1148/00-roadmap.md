# Roadmap: PYPOST-1148

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1148/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1148/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import_teardown_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Update `CollectionImportActions` in `pypost/ui/presenters/collection_import_actions.py` (`is_busy` checks `_worker is not None`, `wait_idle` flushes deferred deletes, and `teardown` safely disconnects, waits, joins, and reaps workers).
  - [x] Iteration 2: Implement `teardown` on `CollectionsPresenter` (`pypost/ui/presenters/collections_presenter.py`) delegating to `_import_actions.teardown` and closing panel.
  - [x] Iteration 3: Update `tests/test_collection_import_async_gaps.py` to synchronize async operations via `wait_import_idle()` and invoke `presenter.teardown()` in cleanup blocks; verify tests and gates.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1148/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1148/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1148/60-tech-debt.md`
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

- `ai-tasks/PYPOST-1148/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1148/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1148/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1148/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1148/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
