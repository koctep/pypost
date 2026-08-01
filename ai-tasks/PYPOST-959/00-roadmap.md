# Roadmap: PYPOST-959

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_http.py::test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method`
- [x] **STEP 4: Development**
  - [x] Uppercase request method in `_resolve_url_router_response` compound lookup
  - [x] Updated `doc/dev/agent_e2e_http.md` match rules (Step 8)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-959/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-959/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_http.py::test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method`

### STEP 4: Development

- `pypost/fixtures/agent_e2e_http.py`
- `tests/test_agent_e2e_http.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-959/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-959/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-959/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`
- `ai-tasks/PYPOST-959/70-dev-docs.md`

Suggested branch (reference): `debt/PYPOST-959-method-case-normalization`
