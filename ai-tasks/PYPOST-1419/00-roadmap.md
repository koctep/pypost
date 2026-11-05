# Roadmap: PYPOST-1419

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1419/10-requirements.md`
  - [x] Documented business goals, user stories, DoD, scope, and Q&A for
    SharedVenvManager encapsulation
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1419/20-architecture.md`
  - [x] Modules: `SharedVenvManager` in `tests/helpers/shared_venv_manager.py`;
    thin facades in `tests/makefile_test_helpers.py`
  - [x] Patterns: cohesive manager, constructor DI, default instance by convention,
    stable facades; preserve skeleton/`.pth` materialization
  - [x] Step 3 failing-repro plan: `tests/test_shared_venv_manager.py` (ownership +
    isolated DI stages; red via missing module / unmet ownership assertions)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_shared_venv_manager.py`
- [x] **STEP 4: Development**
  - [x] Implemented `SharedVenvManager` in `tests/helpers/shared_venv_manager.py`
    (bootstrap, flock+budget lock, skeleton publish, owned readiness, materialize)
  - [x] Wired thin facades + lazy default manager in `tests/makefile_test_helpers.py`;
    removed module-level `_SHARED_BASE_VENV` path-cache SoT
  - [x] Adapted `tests/test_makefile_shared_readiness.py` to manager readiness seams
  - [x] Green: `tests/test_shared_venv_manager.py` + `tests/test_makefile_shared_readiness.py`;
    `make lint` OK
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1419/40-code-cleanup.md`
  - Docstring / readability cleanup in scoped manager + tests; `_module_tempdir`
    late-bind seam; `make lint` OK; focused readiness + manager tests green
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1419/50-observability.md`
  - Observability intentionally minimal for test-helper encapsulation:
    fail-loud stage-scoped `RuntimeError` diagnostics; no production
    logger/metrics (same philosophy as PYPOST-1413 / PYPOST-1429)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1419/60-tech-debt.md`
  - SharedVenvManager residual debt documented (facades/shims, `cp -a`, readiness depth)
  - Triaged Step 4 make-check failures via throwaway worktree at
    `3fa5cf6bd68cff8a31e75bb1276cf9b9e017fade`: lockfile confirmed pre-existing
    (PYPOST-1397); Qt exit -11/-7 not reproduced at clean baseline (environment-sensitive)
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/shared_venv_materialization.md` for SharedVenvManager + facades
  - Aligned `doc/dev/testing.md`, `doc/dev/README.md`, `doc/dev/parallel_test_runner.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1419/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1419/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_shared_venv_manager.py` (red: missing `tests.helpers.shared_venv_manager`)

### STEP 4: Development

- `tests/helpers/shared_venv_manager.py` — `SharedVenvManager`
- `tests/makefile_test_helpers.py` — thin facades + lazy default manager
- `tests/test_makefile_shared_readiness.py` — adapted to manager readiness seams
- Green gate: `tests/test_shared_venv_manager.py`,
  `tests/test_makefile_shared_readiness.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1419/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1419/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1419/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/shared_venv_materialization.md` — SharedVenvManager ownership, facades, API,
  configuration, troubleshooting (PYPOST-1413 layout preserved)
- `doc/dev/testing.md` — shared Make fixture section updated for PYPOST-1419
- `doc/dev/README.md` — index entry includes PYPOST-1419
- `doc/dev/parallel_test_runner.md` — skeleton/`cp -a` + manager pointer (was stale `cp -al`)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
