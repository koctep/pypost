# Roadmap: PYPOST-166

**Language:** Python

**Branch (reference):** `refactoring/PYPOST-166-metrics-declarative-routing`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified PYPOST-75 split removed manual `PATH_INFO` wrapper from `MetricsManager`
  - [x] Confirmed `MetricsServer._create_app()` uses Starlette `Mount("/metrics")`
  - [x] Existing ASGI compatibility tests cover declarative routing (no new code required)
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

- `ai-tasks/PYPOST-166/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-166/20-architecture.md`

### STEP 3: Development

- Verification only — no source changes (resolved by PYPOST-49/75)
- `tests/test_mcp_asgi_compatibility.py` — existing `/metrics` mount coverage

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-166/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-166/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-166/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `ai-tasks/PYPOST-166/70-dev-docs.md`
