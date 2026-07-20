# Roadmap: PYPOST-821

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extended `tests/test_tab_layout_regression.py` with dark-theme close-icon
    contrast smoke test (static asset + QSS wiring; no production change)
- [x] **STEP 4: Code Cleanup**
  - [x] Test-only; follows existing module patterns; timeout via module `pytestmark`
- [x] **STEP 5: Observability**
  - [x] N/A for production; contract documented in test docstring
- [x] **STEP 6: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-821/60-tech-debt.md` — SAFE TO CLOSE
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/ui_font_and_styles.md` regression coverage note
  - [x] `ai-tasks/PYPOST-821/70-dev-docs.md` created

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-821/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-821/20-architecture.md`

### STEP 3: Development

- `tests/test_tab_layout_regression.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-821/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-821/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-821/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_font_and_styles.md`
- `ai-tasks/PYPOST-821/70-dev-docs.md`
