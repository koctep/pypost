# Roadmap: PYPOST-548

Programming language: Python (.cursor/lsr/do-python.md)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] CHUNK 1: Reordered `_on_request_persisted` so sibling staleness resolves before
    label/name mutation (Layer 1 production fix); regression test hardened to patch
    `prompt_dirty_sibling_tab_reload` and assert it is never called.
  - [x] CHUNK 2: Timeout infrastructure — `Makefile`, `pytest.ini`, `tests/conftest.py`.
  - [x] CHUNK 3: Module-level `pytestmark` on all 77 test files (30/60/120s tiers).
  - [x] CHUNK 4: `make test` — 886 passed in 6.62s; conftest negative check verified.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

**Suggested branch:** `fix/PYPOST-548-make-test-stuck`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-548/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-548/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-548/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-548/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-548/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
