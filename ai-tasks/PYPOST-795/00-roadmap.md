# Roadmap: PYPOST-795

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Document `set_close_button_size` use case; keep API (no production caller)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (existing PyPost desktop application codebase).

## Decision

**Keep and document** `PyPostStyle.set_close_button_size` as an opt-in override. No production
caller after PYPOST-792; removal would drop a deliberate escape hatch and break opt-in regression
tests without user benefit.

## Suggested Branch Name

`documentation/PYPOST-795-close-button-size-api`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-795/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-795/20-architecture.md`

### STEP 3: Development

- `pypost/ui/styles/custom_style.py` — expanded method docstring
- `doc/dev/ui_font_and_styles.md` — explicit when-to-use / when-not-to-use

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-795/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-795/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-795/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_font_and_styles.md`
- `ai-tasks/PYPOST-795/70-dev-docs.md`
