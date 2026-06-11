# Roadmap: PYPOST-390

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `_collection_items_by_id` index maintained on tree rebuild/insert/remove
  - [x] `restore_tree_state` iterates saved expanded ids with O(1) lookup
  - [x] `_find_collection_item` uses index for collection lookups
  - [x] Tests for large collection sets and incremental index sync
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

`performance/PYPOST-390-restore-tree-index`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-390/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-390/20-architecture.md`

### STEP 3: Development

- `pypost/ui/presenters/collections_presenter.py`
- `tests/test_collections_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-390/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-390/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-390/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/collection_tree_actions.md`
