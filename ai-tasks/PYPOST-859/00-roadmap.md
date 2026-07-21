# Roadmap: PYPOST-859

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Shared HTTP catalog + `stub_agent_e2e_http` in
    `pypost/fixtures/agent_e2e_http.py`
  - [x] Pytest fixture `agent_e2e_http_stub` in agent_e2e plugin
  - [x] Unit tests `tests/test_agent_e2e_http.py` (5 passed)
  - [x] Migrated golden onto shared catalog/stub
  - [x] Env seed Send scenario `tests/test_agent_e2e_http_env.py`
  - [x] Verified: `make test-agent-e2e` → 32 passed
- [x] **STEP 4: Code Cleanup**
  - [x] `40-code-cleanup.md`; flake8 clean; timeouts present
- [x] **STEP 5: Observability**
  - [x] `agent_e2e_http_stub_installed name=…`; `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; 4 Low Debt follow-ups listed
- [x] **STEP 7: Dev Docs**
  - [x] `70-dev-docs.md`; `agent_e2e_http.md` + umbrella/golden/env/logging

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the shared HTTP fixture/helper and
agent e2e migration. Developer documentation under `doc/dev/` follows
Markdown guidelines (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-859/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-859/20-architecture.md`
- Catalog + CM in `pypost/fixtures/agent_e2e_http.py`
- Pytest fixture in `tests/_pytest_plugins/agent_e2e.py`
- Patch at RequestService `HTTPClient.send_request` use site

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-859/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-859/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-859/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-859/70-dev-docs.md`
- `doc/dev/` updates (HTTP page, umbrella, golden, env, seed, logging, README)
