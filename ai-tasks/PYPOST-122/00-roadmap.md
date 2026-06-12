# Roadmap: PYPOST-122

**Programming language:** Python (PySide6)

**Suggested branch:** `performance/PYPOST-122-line-scoped-hover-scan`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added line-scoped hover scan in `VariableHoverMixin` (`_slice_line_at_index`,
    `_prepare_hover_scan_context`, `_hover_line_scoped_scan` flag)
  - [x] Enabled line-scoped scan on `VariableAwarePlainTextEdit`
  - [x] Added unit tests for slice helper and large-document hover path
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

- `ai-tasks/PYPOST-122/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-122/20-architecture.md`

### STEP 3: Development

- `pypost/ui/widgets/mixins.py`
- `pypost/ui/widgets/variable_aware_widgets.py`
- `tests/test_variable_hover.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-122/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-122/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-122/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-122/70-dev-docs.md`
- `doc/dev/ui_mixins.md`
