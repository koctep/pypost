# Roadmap: PYPOST-154

**Language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified MCP bind error handling (PYPOST-556, shared `format_bind_error`)
  - [x] Verified metrics bind error handling (PYPOST-153)
  - [x] Added `tests/test_server_bind.py` for shared helper coverage
  - [x] Confirmed UI wiring: `EnvPresenter` (MCP), `MainWindow` (metrics)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-154/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-154/20-architecture.md`

### STEP 3: Development

- `tests/test_server_bind.py` (new shared-helper tests)
- Verification only — implementation delivered in PYPOST-153 / PYPOST-556

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-154/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-154/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-154/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-154/70-dev-docs.md`
