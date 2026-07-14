# Roadmap: PYPOST-797

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Connected `plus_btn.clicked` → `new_tab_requested` in `RequestTabHeader.ensure_plus_tab()`
  - [x] Updated plus-tab tests to `QTest.mouseClick` on real button widget
- [x] **STEP 4: Code Cleanup**
  - [x] flake8 clean on `pypost/ui/widgets/tab_header.py`; test E402 is pre-existing pattern
  - [x] 58/58 tests pass in `test_tab_header.py` and `test_tabs_presenter.py`
  - [x] `ai-tasks/PYPOST-797/40-code-cleanup.md` created
- [x] **STEP 5: Observability**
  - [x] Existing `handle_new_tab` INFO log and `gui_new_tab_actions_total` cover + click path
  - [x] No duplicate logging in `RequestTabHeader` (presenter is aggregation point)
  - [x] `ai-tasks/PYPOST-797/50-observability.md` created
- [x] **STEP 6: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-797/60-tech-debt.md` created
  - [x] User review and approval to proceed to Step 7
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/request_actions.md` for `plus_btn.clicked` primary path
  - [x] `ai-tasks/PYPOST-797/70-dev-docs.md` created
  - [x] User review and approval to close task

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-797/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-797/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-797/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-797/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-797/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/request_actions.md`
- `ai-tasks/PYPOST-797/70-dev-docs.md`
