# Roadmap: PYPOST-961

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Red gap: missing hook best-effort per-type units (test-only)*
- [x] **STEP 4: Development**
  - [x] Added `test_dump_hook_best_effort_per_type` parametrized over
    `DUMP_BEST_EFFORT_ERRORS`
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

- `ai-tasks/PYPOST-961/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-961/20-architecture.md`

### STEP 3: Failing Repro

- Parametrized red gap documented; production hook wrapper already correct
  (PYPOST-914 / PYPOST-960)

### STEP 4: Development

- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-961/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-961/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-961/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`
- `ai-tasks/PYPOST-961/70-dev-docs.md`
