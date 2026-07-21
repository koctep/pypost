# Roadmap: PYPOST-869

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_response_panel.py` (red: missing module + local defs)
- [x] **STEP 4: Development**
  - [x] Add `tests/helpers/agent_e2e_response_panel.py`
  - [x] Rewire four Send consumer modules
  - [x] Green unit + targeted agent e2e (8 smoke Send + 5 unit)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for shared test helpers and rewires;
pytest (`.cursor/lsr/do-testing.md`); English Markdown for ai-tasks /
`doc/dev` (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-869/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-869/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_response_panel.py`

### STEP 4: Development

- `tests/helpers/agent_e2e_response_panel.py`
- Rewired: golden, env Send, double-body, presentation matrix
- Unit + smoke agent e2e green

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-869/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-869/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-869/60-tech-debt.md` — **SAFE TO CLOSE**

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_response_panel.md` (+ index / cross-links)
- `ai-tasks/PYPOST-869/70-dev-docs.md`

## Suggested branch

`refactor/PYPOST-869-shared-response-panel-helpers`
