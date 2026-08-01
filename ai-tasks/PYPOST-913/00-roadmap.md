# Roadmap: PYPOST-913

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_agent_e2e_failure_artifacts.py — red assert on session_source key*
- [x] **STEP 4: Development**
  - [x] *Rename diagnostics key + API kwarg session_fixture → session_source*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (pytest / agent e2e failure artifacts)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-913/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-913/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py` (`test_diagnostics_uses_session_source_key`)

### STEP 4: Development

- `pypost/fixtures/agent_e2e_failure.py`
- `tests/_pytest_plugins/agent_e2e.py`
- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-913/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-913/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-913/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`

## Suggested branch (reference)

`debt/PYPOST-913-session-source-rename`
