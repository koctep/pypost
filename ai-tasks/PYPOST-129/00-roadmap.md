# Roadmap: PYPOST-129

**Language:** Python

**Suggested branch:** `refactoring/PYPOST-129-split-variable-hover-helper`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Split `VariableHoverHelper` into `VariableHoverLocator` and `VariableHoverResolver`
  - [x] Keep `VariableHoverHelper` as backward-compatible facade
  - [x] Wire call sites to locator/resolver where appropriate
  - [x] Add `TestVariableHoverSplit` coverage
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

- `ai-tasks/PYPOST-129/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-129/20-architecture.md`

### STEP 3: Development

- `pypost/ui/widgets/mixins.py`
- `pypost/ui/widgets/variable_aware_widgets.py`
- `pypost/ui/widgets/request_editor.py`
- `tests/test_variable_hover.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-129/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-129/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-129/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_mixins.md`
