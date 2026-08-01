# Roadmap: PYPOST-914

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_agent_e2e_failure_artifacts.py — LookupError propagation red*
- [x] **STEP 4: Development**
  - [x] *Narrow lifecycle dump-hook catch tuple (PYPOST-914)*
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

- `ai-tasks/PYPOST-914/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-914/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py` (`test_dump_hook_propagates_unexpected_exception`)

### STEP 4: Development

- `pypost/agent/lifecycle.py`
- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-914/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-914/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-914/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`, `doc/dev/logging.md`

## Suggested branch (reference)

`debt/PYPOST-914-narrow-lifecycle-dump-hook-exceptions`
