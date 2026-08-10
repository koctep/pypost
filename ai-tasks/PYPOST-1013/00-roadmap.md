# Roadmap: PYPOST-1013

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_collection_tree_actions.py — `test_collection_menu_offers_export_collection` (menu includes Export Collection… for collection row)*
  - [x] *tests/test_collection_tree_actions.py — `test_request_menu_offers_export_collection`*
  - [x] *tests/test_collection_tree_actions.py — dispatch tests pass clicked index to export callback*
- [x] **STEP 4: Development**
  - [x] *CollectionExportActions accepts optional clicked `source_index` (button keeps currentIndex)*
  - [x] *CollectionTreeActions menu offers Export Collection… on collection and request rows*
  - [x] *CollectionsPresenter wires tree callback to shared export orchestration*
  - [x] *Updated action_count helpers/tests (3 collection / 4 request) and docs*
  - [x] *Step 3 red tests green; dispatch coverage added*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1013/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1013/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_tree_actions.py`
  (`test_collection_menu_offers_export_collection`,
  `test_request_menu_offers_export_collection`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1013/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1013/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1013/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_export.md` — dual entry points, `source_index`, logging, API
- `doc/dev/collection_tree_actions.md` — menu order, export callback, action_count
- `doc/dev/logging.md` — `collection_export_*` catalog events
- `doc/dev/README.md` — Collection Export TOC entry
- `doc/user/collections.md` — user-facing export (button + context menu; Step 4)
- Related consistency: `collection_import.md`, `collection_item_rename.md`,
  `collection_item_delete.md`

## Suggested branch

`feature/PYPOST-1013-context-menu-export-collection`
