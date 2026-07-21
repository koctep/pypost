# Roadmap: PYPOST-871

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_http.py::test_seed_post_gui_send_scenario_module_exists`
- [x] **STEP 4: Development**
  - [x] Add `tests/test_agent_e2e_http_seed_post.py` GUI Send scenario
  - [x] Inventory gate green; GUI Send green under `make test-agent-e2e`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the agent e2e Send scenario;
pytest (`.cursor/lsr/do-testing.md`); English Markdown for ai-tasks /
`doc/dev` (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-871/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-871/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_http.py::test_seed_post_gui_send_scenario_module_exists`

### STEP 4: Development

- `tests/test_agent_e2e_http_seed_post.py`
- Inventory + GUI Send green

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-871/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-871/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-871/60-tech-debt.md` — **SAFE TO CLOSE**

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`, `doc/dev/agent_e2e.md`
- `ai-tasks/PYPOST-871/70-dev-docs.md`

## Suggested branch

`test/PYPOST-871-seed-post-gui-send`
