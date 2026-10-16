# Roadmap: PYPOST-1411

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals, user stories, acceptance criteria, and domain entities for workspace environment variable import action from collections
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1411/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design architecture for workspace environment variable import action from collections in `ai-tasks/PYPOST-1411/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_workspace_environment_import_repro.py`
- [x] **STEP 4: Development**
  - [x] Implemented collection variable import domain engine (`pypost/core/collection_variable_import.py`) with preset evaluation, name validation, conflict strategies (skip/overwrite), and secret masking
  - [x] Registered widget IDs for import UI (`pypost/ui/widget_ids.py`)
  - [x] Implemented `ImportCollectionVariablesDialog` (`pypost/ui/dialogs/import_collection_variables_dialog.py`) with collection source & preset selector, preview table with secret masking, collision badges, selective row checkboxes, and conflict resolution options
  - [x] Integrated import button in `EnvironmentVariablesWidget` (`pypost/ui/widgets/environments/environment_variables_widget.py`) and updated `EnvironmentDialog` and `EnvironmentPresenter`
  - [x] All 10 reproduction tests in `tests/test_workspace_environment_import_repro.py` passing GREEN
  - [x] Synchronized dialog inventory audit and baseline metrics (`make verify-ai-tasks`, `make lint`, `make typecheck`, `make test`)
- [x] **STEP 5: Code Cleanup**
  - [x] Code cleanup, formatting, and quality checks completed in `ai-tasks/PYPOST-1411/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Structured logging, secret-safe logging contract, and observability tests documented in `ai-tasks/PYPOST-1411/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1411/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Developer documentation created in `doc/dev/workspace_environment_variable_import.md` and referenced in `doc/dev/README.md`, `doc/dev/environments_dialog.md`, and `doc/dev/collection_scoped_variables.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1411/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1411/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1411/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1411/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1411/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
