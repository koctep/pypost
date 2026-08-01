# Roadmap: PYPOST-949

**Branch (reference):** `feature/PYPOST-949-tab-scoped-wait-for-text`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red: `tests/test_ui_wait.py` — `test_session_wait_for_text_in_current_tab_after_multi_tab_send`
- [x] **STEP 4: Development**
  - [x] `in_current_tab` on `AgentAppSession.wait_for_text` / `wait_for_widget` / `wait_for_enabled`
  - [x] `wait_response_after_send` uses session text waits when tab-scoped
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-949/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-949/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_wait.py` — multi-tab Send tab-scoped text wait

### STEP 4: Development

- `pypost/agent/lifecycle.py`
- `tests/helpers/agent_e2e_send_settle.py`
- `tests/test_ui_wait.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-949/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-949/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-949/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_wait.md`
- `doc/dev/agent_e2e_send_settle.md`
