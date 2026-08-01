# Roadmap: PYPOST-906

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *`tests/test_makefile.py`: `test_lint_depends_on_marker_and_venv_test` + `test_run_depends_on_marker_only`*
- [x] **STEP 4: Development**
  - [x] Added `venv-test` to `lint` prereqs (mirror typecheck); left `run` marker-only
  - [x] Rewrote bare-venv lint smoke to expect ensure-and-succeed
  - [x] Confirmed Step 3 lint prereq test + makefile suite green
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean; line length ≤100 on edited files
  - [x] `tests/test_makefile.py` green (48 passed, 1 deselected)
  - [x] `ai-tasks/PYPOST-906/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] App logging N/A (Makefile tooling only)
  - [x] Documented operator-visible Make behavior (pip on first bare lint;
        skip when stamp current per PYPOST-905)
  - [x] `ai-tasks/PYPOST-906/50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-906/60-tech-debt.md` (SAFE TO CLOSE; docs → Step 8)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md` + `doc/dev/setup.md` (lint → `venv-test`; run marker-only)
  - [x] `ai-tasks/PYPOST-906/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Makefile (root build interface) with Python pytest contract / smoke tests
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-906/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-906/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-906/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-906/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-906/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`, `doc/dev/setup.md`
- `ai-tasks/PYPOST-906/70-dev-docs.md`
