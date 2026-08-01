# Roadmap: PYPOST-940

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_qt_item_view_teardown.py` — red until shared helper exists
- [x] **STEP 4: Development**
  - [x] `tests/helpers/qt_item_view.py` — `detach_item_view_model`, `close_item_view_fixture`
  - [x] `tests/test_ui_actions.py` — tree/list fixtures use shared teardown
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-940/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-940/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_qt_item_view_teardown.py`

### STEP 4: Development

- `tests/helpers/qt_item_view.py`
- `tests/test_ui_actions.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-940/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-940/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-940/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (GUI fixture teardown section)
