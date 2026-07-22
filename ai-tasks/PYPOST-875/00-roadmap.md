# Roadmap: PYPOST-875

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_failure_artifacts.py::test_dumps_on_direct_session_assert_fail` (red then green)
- [x] **STEP 4: Development**
  - [x] Optional `AgentAppSession.__exit__` failure-dump hook
  - [x] ContextVar nodeid + plugin install / per-test bind
  - [x] Direct-construction subprocess proof green (8/8 module)
  - [x] Docs: failure artifacts, agent_e2e, lifecycle, logging
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest harness / agent e2e fixtures); developer docs in English
Markdown. Guides: `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`,
`.cursor/lsr/do-markdown.md`.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-875/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-875/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py::test_dumps_on_direct_session_assert_fail`

### STEP 4: Development

- `pypost/agent/lifecycle.py`
- `pypost/fixtures/agent_e2e_failure.py`
- `tests/_pytest_plugins/agent_e2e.py`
- `tests/test_agent_e2e_failure_artifacts.py`
- Docs under `doc/dev/`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-875/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-875/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-875/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-875/70-dev-docs.md`
- Updates under `doc/dev/`
