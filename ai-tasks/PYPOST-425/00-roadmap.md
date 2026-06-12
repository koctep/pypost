# Roadmap: PYPOST-425

Programming language: Python 3 (PySide6)

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Confirm `MainWindow.apply_settings` has no per-widget `setFont` loop (done in PYPOST-106)
  - [x] Remove redundant `EnvPresenter.apply_font` widget loop
  - [x] Clean stale test stubs referencing removed main-window loop
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

- `ai-tasks/PYPOST-425/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-425/20-architecture.md`

### STEP 3: Development

- `pypost/ui/presenters/env_presenter.py`
- `tests/test_apply_settings_font.py`
- `tests/test_env_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-425/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-425/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-425/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-425/70-dev-docs.md`
- `doc/dev/ui_font_and_styles.md`
- `doc/dev/environments_dialog.md`

## Branch (reference)

`refactoring/PYPOST-425-remove-redundant-font-loop`
