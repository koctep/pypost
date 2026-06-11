# Roadmap: PYPOST-387

**Suggested branch:** `refactoring/PYPOST-387-collection-item-type-check`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `_is_collection_item` helper on `CollectionsPresenter`
  - [x] Replaced repeated `isinstance(data, str)` in expand/collapse/restore paths
  - [x] Added presenter unit tests for the helper
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 UI, unittest)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-387/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-387/20-architecture.md`

### STEP 3: Development

- `pypost/ui/presenters/collections_presenter.py`
- `tests/test_collections_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-387/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-387/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-387/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-387/70-dev-docs.md`
- `doc/dev/collection_tree_actions.md`
