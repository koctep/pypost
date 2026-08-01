# Roadmap: PYPOST-916

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ui_actions.py` — list select by text/index (red confirmed)
- [x] **STEP 4: Development**
  - [x] Extended `ui_select` for `QListWidget` / `QTreeView` + `str | int`
  - [x] Session helper + fixture tests (list, tree, combo index) green
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 agent UI actions)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-916/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-916/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions.py` (`test_ui_select_list_by_text`,
  `test_ui_select_list_by_index`)

### STEP 4: Development

- `pypost/agent/ui_actions.py`
- `pypost/agent/lifecycle.py`
- `tests/test_ui_actions.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-916/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-916/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-916/60-tech-debt.md` — **SAFE TO CLOSE**

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `doc/dev/agent_e2e_seed.md`
- `ai-tasks/PYPOST-916/70-dev-docs.md`
