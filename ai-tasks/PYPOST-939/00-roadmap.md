# Roadmap: PYPOST-939

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ui_actions.py::test_ui_select_list_view_by_text` (red before Step 4)
- [x] **STEP 4: Development**
  - [x] `_select_item_view` dispatch for `QListView` / model-backed `QAbstractItemView`
  - [x] Green list-view tests; combo/list/tree regressions unchanged
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6), English Markdown developer docs.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-939/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-939/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions.py` — `test_ui_select_list_view_by_text`,
  `test_ui_select_list_view_by_index`

### STEP 4: Development

- `pypost/agent/ui_actions.py`
- `pypost/agent/lifecycle.py` (docstring)
- `tests/test_ui_actions.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-939/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-939/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-939/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `ai-tasks/PYPOST-939/70-dev-docs.md`
