# Roadmap: PYPOST-955

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  *(marked complete directly; `[/]` in-progress marker abbreviated under
  sprint-task-runner Step 1 autonomy)*
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_http.py::test_mapping_multi_url_settle_timeout_companion_exists` — inventory gate; red until companion callable in mapping module
- [x] **STEP 4: Development**
  - [x] Added `test_mapping_get_send_settle_timeout_includes_step_and_excerpt` — forced GET Send settle timeout with inline rewrap; asserts `step` + `response_excerpt`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-955/50-observability.md` — test-only companion; inherits PYPOST-901 timeout diagnostics contract; no new production logging
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-955/60-tech-debt.md` — GET companion closes PYPOST-901 TD-1; optional POST companion + Step 8 doc noted
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/agent_e2e_http.md` — mapping multi-URL two-test table; GET timeout companion (955)
  - [x] `ai-tasks/PYPOST-955/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (agent e2e timeout companion tests); Markdown for task artifacts

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-955/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-955/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-955/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-955/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-955/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`
- `ai-tasks/PYPOST-955/70-dev-docs.md`
