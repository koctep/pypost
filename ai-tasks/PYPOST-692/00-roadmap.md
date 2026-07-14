# Roadmap: PYPOST-692

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-692-move-style-manager-to-ui`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Move `StyleManager` to `pypost/ui/styles/style_manager.py`
  - [x] Update `main_window.py` and test imports
  - [x] Delete `pypost/core/style_manager.py`
  - [x] `make check` passes
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

- `ai-tasks/PYPOST-692/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-692/20-architecture.md`

### STEP 3: Development

- `pypost/ui/styles/style_manager.py`
- `pypost/ui/main_window.py`
- `tests/test_style_manager_theme.py`
- `tests/test_style_manager_font.py`
- `tests/test_tab_layout_regression.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-692/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-692/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-692/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-692/70-dev-docs.md`
- `doc/dev/architecture.md`
- `doc/dev/architecture_audit.md`
- `doc/dev/ui_font_and_styles.md`
