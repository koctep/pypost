# Roadmap: PYPOST-536

Suggested branch: `refactoring/PYPOST-536-unify-hover-tokenizer`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Export `TEMPLATE_PLACEHOLDER_PATTERN`; wire `VariableHoverHelper.EXPRESSION_PATTERN` to it
  - [x] Add parity tests for hover vs tokenizer
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

- `ai-tasks/PYPOST-536/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-536/20-architecture.md`

### STEP 3: Development

- `pypost/core/template_expression_tokenizer.py`
- `pypost/ui/widgets/mixins.py`
- `tests/test_variable_hover.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-536/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-536/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-536/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/template_expression_functions.md`
- `ai-tasks/PYPOST-536/70-dev-docs.md`
