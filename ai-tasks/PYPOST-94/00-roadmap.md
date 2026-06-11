# Roadmap: PYPOST-94

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `restore_tree_state` uses `_collection_items_by_id` (implemented in PYPOST-390)
  - [x] No full root-level scan remains; O(expanded) restore confirmed in code review
  - [x] Existing PYPOST-390/388/389/391 tests cover behavior and performance path
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6)

## Suggested Branch Name

`performance/PYPOST-94-restore-tree-linear-search`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-94/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-94/20-architecture.md`

### STEP 3: Development

- Verification only — fix landed in PYPOST-390 (`pypost/ui/presenters/collections_presenter.py`)
- `tests/test_collections_presenter.py` (existing coverage)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-94/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-94/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-94/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/collection_tree_actions.md`
- `ai-tasks/PYPOST-94/70-dev-docs.md`
