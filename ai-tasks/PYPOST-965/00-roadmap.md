# Roadmap: PYPOST-965

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — refactor only; duplication is the defect, not runtime behavior
- [x] **STEP 4: Development**
  - [x] Shared `_materialize_slow_smoke_workspace`; fixture and contract test wired
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest test helpers, `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-965/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-965/20-architecture.md`

### STEP 3: Failing Repro

- N/A — structural deduplication; existing contract tests guard behavior

### STEP 4: Development

- `tests/test_makefile.py` — `_materialize_slow_smoke_workspace`
- `tests/test_makefile_install_seed_contract.py` — import shared helper; remove duplicate

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-965/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-965/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-965/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
