# Roadmap: PYPOST-106

Programming language: Python 3 (PySide6)

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Pass `font_size` into `StyleManager.apply_styles` with global `QWidget` QSS rule
  - [x] Remove manual per-widget `setFont` loop from `MainWindow.apply_settings`
  - [x] Extend `test_apply_settings_font.py` and add `test_style_manager_font.py`
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

- `ai-tasks/PYPOST-106/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-106/20-architecture.md`

### STEP 3: Development

- `pypost/core/style_manager.py`
- `pypost/ui/main_window.py`
- `tests/test_apply_settings_font.py`
- `tests/test_style_manager_font.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-106/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-106/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-106/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-106/70-dev-docs.md`
- `doc/dev/ui_font_and_styles.md`
