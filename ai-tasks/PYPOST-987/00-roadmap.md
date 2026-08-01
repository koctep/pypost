# Roadmap: PYPOST-987

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import.py` — red: collection fails with
    `ModuleNotFoundError: No module named 'pypost.core.collection_import'`
  - [x] Reviewed by a separate review subagent: PASS, no test-only fixes needed.
- [x] **STEP 4: Development**
  - [x] Pure core: `pypost/core/collection_import.py` (parse, conflicts,
        id reservation, plan, summary) + `collection_messages.py` +
        `import_conflicts.py` (shared with environment import)
  - [x] Apply layer: `pypost/core/collection_import_apply.py`
  - [x] Qt shell: `pypost/ui/presenters/collection_import_actions.py`,
        Import Collection button in the collections sidebar panel,
        four dialogs in `pypost/ui/collection_item_dialogs.py`
  - [x] `tests/test_collection_import.py` green (23 tests) plus
        `test_collection_import_apply.py` (3) and
        `test_collections_import_ui.py` (14)
  - [x] `make test`: 1994 passed, 21 deselected
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt** — verdict: SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**

## Language

- **Programming language**: Python (existing pypost desktop application)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-987/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-987/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-987/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-987/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-987/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/user/collections.md`
- `doc/dev/`
- `ai-tasks/PYPOST-987/70-dev-docs.md`

## Suggested branch name

`feature/PYPOST-987-import-collection`
