# Roadmap: PYPOST-257

Debt follow-up from [PYPOST-29](https://pypost.atlassian.net/browse/PYPOST-29): Plus button and Ctrl+N new-tab parity.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Unified new-tab entry point through presenter handler
  - [x] Ctrl+N shortcut wired in MainWindow to same path as plus tab click
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

- `ai-tasks/PYPOST-257/10-requirements.md`

### STEP 3: Development

- `pypost/ui/main_window.py`
- `pypost/ui/presenters/tabs_presenter.py`

### STEP 6: Review

- `ai-tasks/PYPOST-257/60-tech-debt.md`
