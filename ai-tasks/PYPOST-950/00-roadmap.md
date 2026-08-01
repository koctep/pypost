# Roadmap: PYPOST-950

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_golden_e2e.py::test_agent_golden_settle_timeout_includes_step_and_excerpt` — assert text-wait diagnostics (`widget_id`, `expected`); red on snapshot path
- [x] **STEP 4: Development**
  - [x] Replaced forced `wait_for_snapshot` miss with tab-scoped `wait_for_text` miss on `RESPONSE_STATUS`; kept `step` + `response_excerpt` wrapping
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest + PySide6 agent e2e harness)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-950/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-950/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_golden_e2e.py` (red assertions on snapshot path)

### STEP 4: Development

- `tests/test_agent_golden_e2e.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-950/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-950/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-950/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_golden_e2e.md`

## Suggested branch

`test/PYPOST-950-timeout-diagnostics-text-wait`
