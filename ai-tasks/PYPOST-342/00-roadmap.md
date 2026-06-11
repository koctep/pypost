# Roadmap: PYPOST-342

Programming language: Python (.cursor/lsr/do-python.md)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] CHUNK 1: `patch_rename_context_menu` helper in `tests/helpers/collections_tree.py`
  - [x] CHUNK 2: `test_collection_tree_rename_context_menu.py` — isolated context-menu
    dispatch and rename lifecycle metrics
  - [x] CHUNK 3: `test_collection_tree_rename_metrics.py` — presenter-level error/not_found/
    rejected_empty/cancelled metrics
  - [x] CHUNK 4: Presenter integration tests for context-menu rename inline edit
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

- `ai-tasks/PYPOST-342/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-342/20-architecture.md`

### STEP 3: Development

- `tests/helpers/collections_tree.py`
- `tests/test_collection_tree_rename_context_menu.py`
- `tests/test_collection_tree_rename_metrics.py`
- `tests/test_collections_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-342/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-342/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-342/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/collection_tree_actions.md`
- `ai-tasks/PYPOST-342/70-dev-docs.md`
