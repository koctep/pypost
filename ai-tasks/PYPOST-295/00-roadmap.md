# Roadmap: PYPOST-295

Debt follow-up from [PYPOST-32](https://pypost.atlassian.net/browse/PYPOST-32): Extract RequestTabHeader; TabsPresenter orchestration.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Tab-header UI logic moved out of `MainWindow`
  - [x] `TabsPresenter` coordinates attach, insert, and new-tab flows
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

- `ai-tasks/PYPOST-295/10-requirements.md`

### STEP 3: Development

- `pypost/ui/widgets/tab_header.py`
- `pypost/ui/presenters/tabs_presenter.py`

### STEP 6: Review

- `ai-tasks/PYPOST-295/60-tech-debt.md`
