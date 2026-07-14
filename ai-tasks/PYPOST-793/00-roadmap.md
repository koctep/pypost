# Roadmap: PYPOST-793

**Branch (reference):** `debt/PYPOST-793-consolidate-style-bootstrap`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `StyleManager.apply_appearance` (theme → QSS → font pipeline)
  - [x] `MainWindow.apply_settings` delegates appearance to `apply_appearance`
  - [x] Added `tests/test_style_manager_appearance.py`; updated `test_apply_settings_font.py`
- [x] **STEP 4: Code Cleanup**
  - [x] Fixed pre-existing E501 in `tabs_presenter_worker.py`
  - [x] `make check` passes (1569 tests)
  - [x] `ai-tasks/PYPOST-793/40-code-cleanup.md`
- [x] **STEP 5: Observability**
  - [x] Documented `apply_appearance` DEBUG logging
  - [x] `ai-tasks/PYPOST-793/50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-793/60-tech-debt.md`
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/ui_font_and_styles.md` for `apply_appearance`
  - [x] `ai-tasks/PYPOST-793/70-dev-docs.md`

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-793/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-793/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-793/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-793/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-793/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_font_and_styles.md`
- `ai-tasks/PYPOST-793/70-dev-docs.md`
