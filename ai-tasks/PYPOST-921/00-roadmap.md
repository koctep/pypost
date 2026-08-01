# Roadmap: PYPOST-921

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red: `tests/test_agent_golden_e2e.py`
    (`test_agent_golden_plus_tab_create_when_no_blank_tab`) —
    `UiTargetNotFoundError: pypost_plus_tab_button`
- [x] **STEP 4: Development**
  - [x] Added `PLUS_TAB_BUTTON`; stamped on plus `QPushButton` in
    `ensure_plus_tab`
  - [x] Golden plus-tab create scenario green (strip orphans +
    `ui_click` + Send settle); header unit id lock
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/agent_golden_e2e.md` — plus-tab create path
  - [x] `doc/dev/ui_identity.md` — `PLUS_TAB_BUTTON`
  - [x] `doc/dev/request_actions.md` — button id note
  - [x] `ai-tasks/PYPOST-921/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-921/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-921/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_golden_e2e.py` —
  `test_agent_golden_plus_tab_create_when_no_blank_tab`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-921/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-921/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-921/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_golden_e2e.md`
- `doc/dev/ui_identity.md`
- `doc/dev/request_actions.md`
- `ai-tasks/PYPOST-921/70-dev-docs.md`
