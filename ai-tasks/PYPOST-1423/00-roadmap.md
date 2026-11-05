# Roadmap: PYPOST-1423

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1423/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1423/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_import_collection_variables_module_extract_repro.py` — red then green for LOC < 500 OR classes in target modules
- [x] **STEP 4: Development**
  - [x] Extracted `CollectionVariablesTableModel` (+ COL_*/HEADERS/row record) → `pypost/ui/models/`
  - [x] Extracted `ConflictStrategyDelegate` → `pypost/ui/delegates/`
  - [x] Extracted `CollectionVariablesTableView` (+ proxies) → `pypost/ui/views/`
  - [x] Extracted `CollectionFetchWorker` → `pypost/ui/workers/`
  - [x] Dialog re-exports preserved; related import/virtualization tests green
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` passed; `40-code-cleanup.md` written
- [x] **STEP 6: Observability**
  - [x] Logger channels follow new modules; event names unchanged (`50-observability.md`)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `60-tech-debt.md` with unticketed follow-ups (dialog still ~637 LOC)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/workspace_environment_variable_import.md` module paths
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1423/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1423/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_import_collection_variables_module_extract_repro.py`

### STEP 4: Development

- `pypost/ui/models/collection_variables_table_model.py`
- `pypost/ui/delegates/conflict_strategy_delegate.py`
- `pypost/ui/views/collection_variables_table_view.py`
- `pypost/ui/workers/collection_fetch_worker.py`
- `pypost/ui/dialogs/import_collection_variables_dialog.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1423/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1423/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1423/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
