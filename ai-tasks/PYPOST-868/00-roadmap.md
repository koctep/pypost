# Roadmap: PYPOST-868

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_agent_e2e_http.py — URL router map hit/miss (red confirmed)*
- [x] **STEP 4: Development**
  - [x] *ENABLE: Mapping overload + url_router_side_effect on stub_agent_e2e_http*
  - [x] *Prefer str .url when extracting request_data (MagicMock-safe)*
  - [x] *Unit tests green (9 passed)*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (fixture helper / unit tests); Markdown for developer docs

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-868/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-868/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_http.py`
  (`test_stub_agent_e2e_http_url_router_map`,
  `test_stub_agent_e2e_http_url_router_miss_raises`)

### STEP 4: Development

- `pypost/fixtures/agent_e2e_http.py`
- `tests/test_agent_e2e_http.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-868/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-868/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-868/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`
- `ai-tasks/PYPOST-868/70-dev-docs.md`
