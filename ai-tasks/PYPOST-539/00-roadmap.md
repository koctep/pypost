# Roadmap: PYPOST-539

Suggested branch: `refactoring/PYPOST-539-shared-messagebox-helpers`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extended `collection_item_dialogs.py` with tab, environment, and history helpers
  - [x] Migrated `tabs_presenter`, `env_dialog`, and `history_panel` off direct QMessageBox
  - [x] Updated unit tests and patch targets
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-539/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-539/20-architecture.md`

### STEP 3: Development

- `pypost/ui/collection_item_dialogs.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `pypost/ui/dialogs/env_dialog.py`
- `pypost/ui/widgets/history_panel.py`
- `tests/test_collection_item_dialogs.py`
- `tests/test_tabs_presenter.py`
- `tests/test_env_dialog.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-539/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-539/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-539/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/collection_tree_actions.md`
