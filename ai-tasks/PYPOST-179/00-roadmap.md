# Roadmap: PYPOST-179

**Language:** Python

**Suggested branch:** `feature/PYPOST-179-mcp-test-fixture-generator`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/fixtures/mcp_test_fixtures.py` with programmatic builders
  - [x] Added `scripts/generate_mcp_test_fixtures.py` CLI with `--check`
  - [x] Added `tests/test_generate_mcp_test_fixtures.py`
  - [x] Regenerated `examples/collections/mcp.json` and `config/test/environments.json`
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

- `ai-tasks/PYPOST-179/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-179/20-architecture.md`

### STEP 3: Development

- `pypost/fixtures/mcp_test_fixtures.py`
- `scripts/generate_mcp_test_fixtures.py`
- `tests/test_generate_mcp_test_fixtures.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-179/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-179/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-179/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-179/70-dev-docs.md`
- `doc/dev/testing.md`
- `config/test/README.md`
