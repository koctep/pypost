# Roadmap: PYPOST-465

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pytest-timeout` to CI main job "Install test tools" step (`.github/workflows/test.yml`) — closes local/CI parity gap identified in architecture Phase 2
  - [x] Full local regression after `make clean && make install` (Python 3.14.5, macOS default `python3`): `make test` → **1197 passed, 0 failed**, 1 deselected, 51 subtests (~80s)
  - [x] `make test-slow` → **1 passed, 0 failed** (Makefile install smoke with real `requirements.txt`, ~13s)
  - [x] `make test-cov` → **1197 passed, 0 failed**, 1 deselected; line coverage **87.44%** (≥70% gate, ~76s)
  - Note: CI matrix uses Python 3.11/3.13; host default is 3.14. Intermittent PySide6 segfault observed on 3.14 in MCP integration tests on some runs; final clean regression run completed green
- [x] **STEP 4: Code Cleanup**
  - [x] Ran `make lint` — pre-existing flake8 issues only; no Python changes in this task
  - [x] `ai-tasks/PYPOST-465/40-code-cleanup.md` created
- [x] **STEP 5: Observability**
  - [x] N/A for infra task — documented existing CI/local visibility; no new logs or metrics
  - [x] `ai-tasks/PYPOST-465/50-observability.md` created
- [x] **STEP 6: Review and Technical Debt**
  - [x] Regression evidence recorded; follow-ups listed as NON-BLOCKER only
  - [x] `ai-tasks/PYPOST-465/60-tech-debt.md` created
- [x] **STEP 7: Dev Docs**
  - [x] Added § Reproducible test environment to `doc/dev/testing.md`
  - [x] Updated `doc/dev/setup.md` install/regression checklist and Python 3.11+ note
  - [x] `ai-tasks/PYPOST-465/70-dev-docs.md` created

## Suggested branch name

`chore/PYPOST-465-test-deps-regression`


- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+ (project test toolchain: Makefile, dependency declarations, CI workflow).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-465/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-465/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-465/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-465/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-465/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testing.md`, `doc/dev/setup.md`
- `ai-tasks/PYPOST-465/70-dev-docs.md`
