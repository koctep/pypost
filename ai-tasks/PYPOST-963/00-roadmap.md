# Roadmap: PYPOST-963

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — policy assertion test; no pre-existing behavioral bug
- [x] **STEP 4: Development**
  - [x] Named minimum-tree policy constant + contract assertion; doc touch
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest contract tests, `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-963/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-963/20-architecture.md`

### STEP 3: Failing Repro

- N/A — extends PYPOST-943 seed contract with explicit minimum-tree assertion

### STEP 4: Development

- `tests/test_makefile.py` — `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` policy constant
- `tests/test_makefile_install_seed_contract.py` — minimum-tree assertion test
- `doc/dev/testing.md` — minimum tree policy section

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-963/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-963/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-963/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
