# Roadmap: PYPOST-826

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `test_handle_close_tab_closes_current` passes (fix already in PYPOST-824)
  - [x] No duplicate production change to `TabsPresenter` (close_tab reselect inherited)
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

- `ai-tasks/PYPOST-826/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-826/20-architecture.md`

### STEP 3: Development

- Source code: none for this ticket (production fix in PYPOST-824
  `pypost/ui/presenters/tabs_presenter.py` `close_tab`)
- Tests: existing `tests/test_tabs_presenter.py::test_handle_close_tab_closes_current`
- Documentation updates: none required beyond PYPOST-824 (see Step 7)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-826/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-826/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-826/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-826/70-dev-docs.md`
- Core docs from PYPOST-824 in `doc/dev/request_actions.md`; unique PYPOST-826
  verification note added on the close-focus troubleshooting bullet

## Language

Python 3.10+

## Coordination

- Sibling tickets: PYPOST-824 (production fix), PYPOST-825 (related entry point).
- This ticket documents verification that `handle_close_tab` inherits the PYPOST-824
  `close_tab` navigable reselect; no second production patch.
