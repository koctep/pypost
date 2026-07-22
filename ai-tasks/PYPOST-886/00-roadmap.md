# Roadmap: PYPOST-886

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_suite_qapp_alignment.py` (priority AST guard; was red, now green)
- [x] **STEP 4: Development**
  - [x] Batch A — workers: `test_request_save_orchestrator.py`, `test_worker_race.py`
  - [x] Batch B — presenters: collections / env / tabs / font-inheritance
  - [x] Batch C — editors: code editor family, tab header, request editor family
  - [x] Batch D — local `def qapp()` dialogs/settings/style (~22 modules)
  - [x] Batch E — remaining `setUpClass` QApplication modules (tree, main window,
    integration, variable hover, bind-host, etc.)
  - [x] Suite inventory clear; alignment guard green; priority cluster **331 passed**
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE; unticketed: TD-3 (optional Lowest)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/gui_testing.md`, `testing.md`, `environment_storage_async.md`
  - [x] Artifact: `ai-tasks/PYPOST-886/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-886/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-886/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_suite_qapp_alignment.py`

### STEP 4: Development

- ~59 migrated `tests/test_*.py` modules + alignment guard
- Shared fixture unchanged: `tests/conftest.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-886/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-886/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-886/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
- `ai-tasks/PYPOST-886/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-886-suite-shared-qapp`
