# Roadmap: PYPOST-1039

**Programming language:** Python

## STEP 1 Approval Record

The applicable `sprint-runner` workflow is autonomous and explicitly
preauthorizes continuation without a separate user gate.  An independent
requirements review passed with no gaps before STEP 1 was marked complete.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [ ] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_jira_mcp_live_smoke.py` and `tests/test_example_fixtures.py`: 4 deterministic red assertions for the absent current-user tool and protected live interface; 9 safety assertions pass.
- [ ] **STEP 4: Development**
  - [ ] *[Add summaries of completed iterations here]*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] HTTPS-only credential transport gate and changed-test flake8 re-review passed; see `60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - [x] Final independent review confirmed the documented four-call contract:
    one current-user dispatch and local result validation, followed by search,
    issue retrieval, and board listing.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1039/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1039/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1039/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1039/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1039/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
- `ai-tasks/PYPOST-1039/70-dev-docs.md`
