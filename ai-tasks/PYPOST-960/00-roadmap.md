# Roadmap: PYPOST-960

**Language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change (refactor only; identity test added in Step 4)
- [x] **STEP 4: Development**
  - [x] Added `pypost/agent/e2e_dump_errors.py` with `DUMP_BEST_EFFORT_ERRORS`
  - [x] Updated `lifecycle.py` and `fixtures/agent_e2e_failure.py` to import shared tuple
  - [x] Added `test_dump_best_effort_errors_shared_module` identity test
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

- `ai-tasks/PYPOST-960/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-960/20-architecture.md`

### STEP 3: Failing Repro

- N/A — refactor with unchanged runtime behavior

### STEP 4: Development

- `pypost/agent/e2e_dump_errors.py`
- `pypost/agent/lifecycle.py`
- `pypost/fixtures/agent_e2e_failure.py`
- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-960/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-960/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-960/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`
- `doc/dev/logging.md`
