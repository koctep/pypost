# Roadmap: PYPOST-1413

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals, user stories, acceptance criteria, and domain entities for resolving Makefile test suite shared venv materialization timeouts under load
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1413/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Analyze materialization bottlenecks and NFS I/O contention in `tests/makefile_test_helpers.py`
  - [x] Design lightweight skeleton template with `.pth` pre-warmed dependency linkage
  - [x] Formulate failing repro test plan for Step 3 exposing timeout under load
  - [x] Document high-level architecture in `ai-tasks/PYPOST-1413/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Implement `_build_skeleton` to stage and publish `.skeleton` containing `pyvenv.cfg`, interpreter symlinks in `bin/`, readiness marker, and `_prewarmed_base.pth` pointing to base venv site-packages
  - [x] Iteration 2: Integrate `.skeleton` lifecycle into `_get_shared_base_venv`, ensuring serialized preparation, cache check, and clean retry handling
  - [x] Iteration 3: Update `_materialize_prewarmed_venv` to clone the lightweight skeleton directory using `cp -a` with fallback to base, cutting file operations by 99.4% and materialization time below 0.3s
  - [x] Iteration 4: Verify Step 3 repro test green, verify `test_makefile_target_install_test.py` and `test_makefile_shared_readiness.py`, and pass repository quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis, format checks, dead code cleanup, and timeout verification
  - [x] Document cleanup in `ai-tasks/PYPOST-1413/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Analyze logging, error context in TimeoutExpired/RuntimeError, durations/telemetry, and diagnostic trace preservation
  - [x] Create `ai-tasks/PYPOST-1413/50-observability.md` documenting observability architecture, error context, and telemetry
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
- [x] **STEP 8: Dev Docs**
  - [x] Document shared virtual environment architecture, lightweight skeleton template, NFS latency resolution, concurrency locking, and workspace isolation in `doc/dev/shared_venv_materialization.md`
  - [x] Link `doc/dev/shared_venv_materialization.md` in `doc/dev/README.md` and cross-reference in `doc/dev/testing.md`
  - [x] Create `ai-tasks/PYPOST-1413/70-dev-docs.md` documenting documentation updates
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1413/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1413/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1413/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1413/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1413/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/shared_venv_materialization.md`
- `doc/dev/README.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-1413/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
