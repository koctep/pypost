# Roadmap: PYPOST-932

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change; regression lock only (Makefile already has typecheck → venv-test)*
- [x] **STEP 4: Development**
  - [x] Added `test_typecheck_depends_on_marker_and_venv_test` mirroring lint peer lock
  - [x] Confirmed makefile contract suite green
- [x] **STEP 5: Code Cleanup**
  - [x] Single focused test; no production edits
  - [x] `ai-tasks/PYPOST-932/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] App logging N/A (contract test only)
  - [x] `ai-tasks/PYPOST-932/50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-932/60-tech-debt.md` (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md` — PYPOST-932 row + dependency-chain row
  - [x] `ai-tasks/PYPOST-932/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python pytest contract tests (`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-932/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-932/20-architecture.md`

### STEP 3: Failing Repro

- N/A — regression lock for existing Makefile edge

### STEP 4: Development

- `tests/test_makefile.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-932/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-932/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-932/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-932/70-dev-docs.md`
