# Roadmap: PYPOST-1045

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Doc lock test on `20-architecture.md` decision markers*
  - Red test: `tests/test_pypost_1045_recommendation_doc_lock.py`
    (`test_pypost_1045_architecture_recommendation_doc_lock`)
- [x] **STEP 4: Development**
  - [x] Added explicit `## Decision Lock` to `20-architecture.md`
    (machine-checkable fields for doc-lock test; no mock server)
  - [x] Confirmed architecture DoD: form, interfaces, Makefile,
    tool-id slice, follow-up sketch complete; no harness code
  - [x] Step 4 review PASS: Decision Lock present, doc-lock green,
    no mock-server implementation
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; flake8/compile/timeout checks; stale
    Step 4 research note aligned
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — N/A (analysis / doc-lock only)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — TD-1 High: loopback collection e2e harness
    (`test-mcp-collection-e2e`); SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - [x] Pointers in `doc/dev/testing.md`, `jira_mcp_live_smoke.md`,
    `agent_e2e.md`, `mcp_integration.md`, `README.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (analysis and any later harness/docs work; no product feature code in this task)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1045/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1045/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1045_recommendation_doc_lock.py`
  — asserts `ai-tasks/PYPOST-1045/20-architecture.md` Decision Lock
  (yes / loopback stand-in / four tool ids / `test-mcp-collection-e2e`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1045/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1045/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1045/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
