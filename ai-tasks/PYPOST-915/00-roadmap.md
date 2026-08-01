# Roadmap: PYPOST-915

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red gap: missing OSError / AttributeError dump best-effort units
- [x] **STEP 4: Development**
  - [x] Added `test_dump_best_effort_on_oserror` and
    `test_dump_best_effort_on_attribute_error` with caplog asserts
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-915/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-915/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py` — red gap documented; full
  asserts added in Step 4 (test-only; production tuple already from PYPOST-876)

### STEP 4: Development

- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-915/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-915/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-915/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`
- `ai-tasks/PYPOST-915/70-dev-docs.md`
