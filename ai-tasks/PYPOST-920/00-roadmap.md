# Roadmap: PYPOST-920

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red: `tests/test_ui_identity_spotcheck.py` (import +
    `findChild` for `RESPONSE_STATUS` / `RESPONSE_BODY`)
  - [x] Red: `tests/test_agent_golden_e2e.py` (`wait_for_text` on
    status/body ids; display-form body)
- [x] **STEP 4: Development**
  - [x] Added `RESPONSE_STATUS` / `RESPONSE_BODY` to catalog +
    `KEY_WIDGET_IDS`; applied via `set_widget_id` in
    `ResponseView.init_ui` (panel id stays in `__init__`)
  - [x] Spot-check + golden e2e green (`wait_for_text` settle;
    display-form body indent=2). Docs deferred to Step 8 (FR7).
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/ui_identity.md` — `RESPONSE_STATUS` / `RESPONSE_BODY`
  - [x] `doc/dev/agent_golden_e2e.md` — `wait_for_text` settle
  - [x] Cross-links: `ui_wait.md`, `agent_e2e_response_panel.md`,
    `agent_e2e.md`
  - [x] `ai-tasks/PYPOST-920/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-920/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-920/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_identity_spotcheck.py` — asserts `RESPONSE_STATUS` /
  `RESPONSE_BODY` via import + `findChild` under `ResponseView`
- `tests/test_agent_golden_e2e.py` — golden settle via `wait_for_text` on
  those ids (display-form body text)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-920/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-920/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-920/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_identity.md`
- `doc/dev/agent_golden_e2e.md`
- `doc/dev/ui_wait.md`, `agent_e2e_response_panel.md`, `agent_e2e.md`
- `ai-tasks/PYPOST-920/70-dev-docs.md`
