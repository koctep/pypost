# Roadmap: PYPOST-942

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. `_select_list` / `_select_tree` already raise
    `UiTargetNotInteractableError` with `option not found` / `option index out of
    range` (see `pypost/agent/ui_actions.py`). Step 4 adds green contract tests in
    `tests/test_ui_actions.py`; no red-before-green cycle required (TD-4 coverage
    debt only).
- [x] **STEP 4: Development**
  - [x] Added four list/tree negative-path contract tests in `tests/test_ui_actions.py`
    mirroring `test_select_missing_option_raises` (missing option + parametrized
    out-of-range indices); full module green (27 passed).
- [x] **STEP 5: Code Cleanup**
  - [x] Reviewed Step 4 negative-path tests; lint clean; 27/27 green; no code
    changes required — see `40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Test-only task — no production logging/metrics; documented in
    `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] Tech debt analysis in `60-tech-debt.md`; SAFE TO CLOSE; closes PYPOST-916 TD-4
- [x] **STEP 8: Dev Docs**
  - [x] Cross-ref list/tree negative-path contract tests in `doc/dev/ui_actions.md`
    and `doc/dev/testing.md`; artifact `70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 agent UI actions and pytest fixtures)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-942/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-942/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-942/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-942/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-942/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-942/70-dev-docs.md`

## Suggested branch

`test/PYPOST-942-list-tree-select-negative-tests`
