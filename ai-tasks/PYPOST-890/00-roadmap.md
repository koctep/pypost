# Roadmap: PYPOST-890

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_presentation_matrix.py` (method × body
    presentation invariants; smoke + slow; red via discard no-op)
  - [x] `ai-tasks/PYPOST-890/findings.md` (failing-cell triage table;
    empty — HEAD 25/25 green)
  - Red proof: temp discard no-op → `POST-json_ok` count=2; restored
    (not committed).
- [x] **STEP 4: Development**
  - [x] Confirmed smoke green under
    `make test-agent-e2e` (5 smoke cells; product fixes out of scope)
  - [x] Hardened Body-tab select: `REQUEST_DETAIL_TABS` identity +
    matrix helper (no RequestWidget walk)
  - [x] FR7 `doc/dev/` matrix note + umbrella links deferred to Step 8
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-890/40-code-cleanup.md` (lint clean; unused
    `RequestWidget` import removed)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-890/50-observability.md` (N/A — no production
    path change)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-890/60-tech-debt.md` (SAFE TO CLOSE; no Jira
    tickets created in this step)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/agent_e2e_presentation_matrix.md` (matrix contract)
  - [x] Umbrella / related links (`agent_e2e.md`, `agent_e2e_http.md`,
    `agent_e2e_double_response_body.md`, `response-streaming-display.md`,
    `ui_identity.md`, `doc/dev/README.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-890/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-890/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_presentation_matrix.py` — method × body presentation
  matrix (smoke + slow); desired once-only body/status asserts
- `ai-tasks/PYPOST-890/findings.md` — failing-cell triage table for PYPOST-891
- Red protocol: temp no-op `_discard_chunk_buffer` (restore; do not commit)

### STEP 4: Development

- Source code (`REQUEST_DETAIL_TABS` + matrix Body-tab harden)
- Tests (`tests/test_agent_e2e_presentation_matrix.py`)
- Documentation updates (FR7 deferred to Step 8)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-890/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-890/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-890/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_presentation_matrix.md`
- Links from `doc/dev/agent_e2e.md`, `agent_e2e_http.md`,
  `agent_e2e_double_response_body.md`, `response-streaming-display.md`,
  `ui_identity.md`, `doc/dev/README.md`
## Suggested branch

`test/PYPOST-890-agent-e2e-presentation-matrix`
