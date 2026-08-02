# Roadmap: PYPOST-974

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change* (`_select_combo` already raises;
    contract test expected green on first run)
- [x] **STEP 4: Development**
  - [x] Added `test_select_combo_index_out_of_range_raises` (param `[-1, 3]`)
  - [x] Updated `doc/dev/ui_actions.md` fixture contract citations
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 agent UI actions and pytest fixtures)

## Suggested branch name (reference only)

`test/PYPOST-974-combo-index-out-of-range`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-974/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-974/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (see architecture)

### STEP 4: Development

- `tests/test_ui_actions.py` — `test_select_combo_index_out_of_range_raises`
- `doc/dev/ui_actions.md` — combo index contract citation

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-974/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-974/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-974/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
