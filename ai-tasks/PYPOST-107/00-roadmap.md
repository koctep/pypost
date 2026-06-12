# Roadmap: PYPOST-107

Programming language: Python 3 (PySide6)

Suggested branch: `refactoring/PYPOST-107-body-editor-font-theme`

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `CodeEditor._refresh_font_metrics` on indent change and `FontChange`
  - [x] `TabsPresenter.apply_settings` docstring — indent/colors only, no font loop
  - [x] `test_font_change_refreshes_tab_stop_distance`
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

- `ai-tasks/PYPOST-107/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-107/20-architecture.md`

### STEP 3: Development

- `pypost/ui/widgets/code_editor.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `tests/test_code_editor.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-107/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-107/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-107/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-107/70-dev-docs.md`
- `doc/dev/ui_font_and_styles.md`
