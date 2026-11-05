# Roadmap: PYPOST-1420

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1420/10-requirements.md`
  - [x] Documented business goals, user stories, DoD, scope, and Q&A for
    native in-process workspace materialization (outcome-focused; no
    implementation approach locked in)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1420/20-architecture.md`
  - [x] Selected in-process `shutil.copytree(..., symlinks=True)` (optional
    `tree_copier` DI); keep `preparation_runner` for bootstrap only
  - [x] Step 3 failing-repro plan: assert `materialize` does not invoke
    `preparation_runner`/`cp` while producing a ready isolated workspace `.venv`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_shared_venv_manager.py::test_materialize_populates_without_preparation_runner_or_cp`
    — red: `materialize` still invokes `preparation_runner` with `cp -a`
    (ready target + isolation asserted; fails on no-`cp` / no-runner gate)
- [x] **STEP 4: Development**
  - [x] Implemented in-process population via `shutil.copytree(..., symlinks=True)`
    with optional `tree_copier` DI; soft `copy_timeout` via injected `_clock`;
    `preparation_runner` retained for bootstrap only
  - [x] Adapted FR5 failure stubs to `tree_copier`; removed `cp` special-cases from
    readiness suite; Step 3 repro + readiness suite green
    (`make test PYTEST_ARGS='tests/test_shared_venv_manager.py tests/test_makefile_shared_readiness.py -q'`)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1420/40-code-cleanup.md`
  - [x] `make lint` clean; focused readiness/manager suites green; docstring/
    soft-timeout except clarity on `materialize`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1420/50-observability.md`
  - [x] Fail-loud materialize diagnostics enriched with `source=` kind and
    soft-deadline `elapsed`; no harness logger noise on healthy path
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1420/60-tech-debt.md`
  - [x] Soft post-copy timeout + silent skeleton fallback documented; `cp -a`
    overhead closed; sibling tickets 1421/1422/1440 referenced; no new
    failing-test NON-BLOCKERs in this batch
- [/] **STEP 8: Dev Docs**
  - [/] `doc/dev/shared_venv_materialization.md` — in-process `shutil.copytree` /
    `tree_copier`; bootstrap-only `preparation_runner`; soft `copy_timeout`
  - [/] `doc/dev/testing.md`, `doc/dev/parallel_test_runner.md`, `doc/dev/README.md`
    — aligned residual `cp -a` narrative with PYPOST-1420
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1420/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1420/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_shared_venv_manager.py::test_materialize_populates_without_preparation_runner_or_cp`
  (red on current `cp -a` via `preparation_runner`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1420/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1420/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1420/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/shared_venv_materialization.md`
- `doc/dev/testing.md`
- `doc/dev/parallel_test_runner.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
