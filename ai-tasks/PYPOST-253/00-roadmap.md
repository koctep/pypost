# Roadmap: PYPOST-253

Debt follow-up from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29): Layout-managed plus tab via RequestTabHeader.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Plus tab rendered as a layout-managed tab marker in `RequestTabHeader`
  - [x] Removed `MainWindow._position_add_tab_button` pixel-offset positioning
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

- `ai-tasks/PYPOST-253/10-requirements.md`

### STEP 3: Development

- `pypost/ui/widgets/tab_header.py`
- `pypost/ui/main_window.py`

### STEP 6: Review

- `ai-tasks/PYPOST-253/60-tech-debt.md`
