# Roadmap: PYPOST-957

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  *(completed under sprint-task-runner Step 1 autonomy)*
- [x] **STEP 2: High-Level Architecture Design**
  *(completed under sprint-task-runner Step 2 autonomy)*
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_http_mapping_multi_url.py` — red
    `pytest.fail` placeholder for Mapping GUI caplog (PYPOST-957)
- [x] **STEP 4: Development**
  - [x] `test_mapping_send_logs_http_stub_installed_url_router` — caplog assert
    `name=url_router` during live Mapping GUI Send
  - [x] Mapping agent e2e suite green (3 tests)
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; `make lint` clean on touched module
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — reuses existing install log; no new events
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/agent_e2e_http.md`; `70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (agent e2e GUI caplog smoke under `tests/`); Markdown for task
artifacts (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-957/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-957/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_http_mapping_multi_url.py` — red placeholder then green
  caplog smoke

### STEP 4: Development

- Source code / tests (test-only)
- Documentation updates (Step 8)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-957/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-957/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-957/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`
