# Roadmap: PYPOST-912

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_agent_e2e_failure_artifacts.py — red gap then caplog assert*
- [x] **STEP 4: Development**
  - [x] *In-process caplog proof for dump-hook WARNING (test-only; no product edit)*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (pytest / caplog / offscreen Qt)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-912/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-912/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py` (`test_dump_hook_failure_logs_warning`)

### STEP 4: Development

- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-912/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-912/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-912/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`, `doc/dev/logging.md`

## Suggested branch (reference)

`debt/PYPOST-912-dump-hook-failed-caplog`
