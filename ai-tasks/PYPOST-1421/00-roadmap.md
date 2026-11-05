# Roadmap: PYPOST-1421

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1421/10-requirements.md`
  - [x] Documented business goals, user stories, DoD, scope, and Q&A for deep
    `_prewarmed_base.pth` readiness validation (outcome-focused)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1421/20-architecture.md`
  - [x] Selected deepen `SharedVenvManager.is_ready` (skeleton requires `.pth`;
    any present `.pth` must point at a readable directory)
  - [x] Step 3 failing-repro plan: assert missing/invalid `.pth` → not ready;
    valid `.pth` → ready
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_shared_venv_manager.py::test_is_ready_rejects_skeleton_without_prewarmed_base_pth`
  - [x] `tests/test_shared_venv_manager.py::test_is_ready_rejects_skeleton_with_invalid_prewarmed_base_pth_target`
  - [x] `tests/test_shared_venv_manager.py::test_is_ready_accepts_skeleton_with_valid_prewarmed_base_pth`
    — red confirmed: `is_ready` returned True for missing/invalid `.pth`;
    valid case already green on shallow check
- [x] **STEP 4: Development**
  - [x] Deepened `SharedVenvManager.is_ready` + `_prewarmed_base_pth_target_ok`
  - [x] Seeded materialize fixtures via `_seed_ready_skeleton`; Step 3 repro +
    readiness suite green
    (`make test PYTEST_ARGS='tests/test_shared_venv_manager.py tests/test_makefile_shared_readiness.py -q'`)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1421/40-code-cleanup.md`
  - [x] `make lint` clean; focused readiness/manager suites green
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1421/50-observability.md`
  - [x] Fail-closed silent readiness predicate; existing materialize/bootstrap
    ERR diagnostics retained; no healthy-path log noise
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1421/60-tech-debt.md`
  - [x] Name-based skeleton rule + no dedicated damage error documented;
    sibling tickets 1422/1440 referenced; no BLOCKER items
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/shared_venv_materialization.md` — deep `.pth` readiness
    (overview, architecture, API table, troubleshooting)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1421/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1421/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_shared_venv_manager.py` (three deep-readiness cases)

### STEP 4: Development

- `tests/helpers/shared_venv_manager.py`
- `tests/test_shared_venv_manager.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1421/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1421/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1421/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/shared_venv_materialization.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
