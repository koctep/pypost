# Roadmap: PYPOST-978

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_response_panel.py`
    `::test_golden_text_waits_use_session_api_not_free_function`
    (GREEN after Step 4 companion migration)
- [x] **STEP 4: Development**
  - [x] Migrated timeout companion to
    `session.wait_for_text(..., in_current_tab=True)`; dropped free
    `wait_for_text` import and unused `tab` binding
  - [x] Convention marker + golden / response-panel selection green
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-978/50-observability.md`
    (N/A for new production logs/metrics; document existing
    `ui_wait_*` + companion diagnostics)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-978/60-tech-debt.md`
    (SAFE TO CLOSE; no new follow-up Jira items; docs → Step 8)
- [x] **STEP 8: Dev Docs**
  - [x] Corrected golden wait guidance:
    `session.wait_for_text(..., in_current_tab=True)` /
    `wait_response_after_send(..., in_current_tab=True)`
    (`ui_wait.md`, `agent_golden_e2e.md`, `agent_e2e.md`)
  - [x] `testing.md` / `ui_actions.md` already accurate (no edits)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (agent e2e / golden harness)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-978/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-978/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_response_panel.py`
  `::test_golden_text_waits_use_session_api_not_free_function`
  (AST convention; expected RED until Step 4)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-978/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-978/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-978/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Suggested branch name

`refactoring/PYPOST-978-golden-tab-scoped-session-wait`
