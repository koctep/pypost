# Roadmap: PYPOST-970

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *RED marker in `tests/test_agent_e2e_response_panel.py`: Golden success helper must
    call shared Send settle; current inline code fails it while runtime tests remain green*
- [x] **STEP 4: Development**
  - [x] *Migrated Golden successful Send settle to `wait_response_after_send` with current-tab,
    message, step, timeout, and diagnostic behavior preserved; focused and agent e2e gates green;
    fast suite has one unrelated artifact-baseline drift failure*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Suggested Branch

`refactoring/PYPOST-970-golden-send-settle`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-970/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-970/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-970/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-970/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-970/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
