# Roadmap: PYPOST-984

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_ci_check_lock_job.py::test_workflow_check_lock_setup_uv_step_pins_version`
    (new) — red: `check-lock` job's `astral-sh/setup-uv` step has no `version:` input yet.
  - `tests/test_makefile_check_lock_retry.py` (new) — red: `make check-lock` has no retry
    loop, no distinct compile-failure/drift messages, and no failure-path scratch-file cleanup.
  - Review: PASS.
- [x] **STEP 4: Development**
  - [x] Pinned `uv` version (`version: "0.11.31"`) on the `astral-sh/setup-uv` step of the
    `check-lock` job in `.github/workflows/test.yml`; cross-referenced the pin in
    `doc/dev/setup.md` § "Dependency lock file (PYPOST-779)" (points at the workflow YAML as
    the single source of truth rather than duplicating the version number).
  - [x] `Makefile` `check-lock` target: wrapped `uv pip compile` in a retry loop (up to 3
    attempts, backoff 1s/2s), emitting a distinct "uv pip compile failed after N attempts"
    message on exhaustion (vs. a distinct "requirements.txt is stale" message on genuine
    `diff` mismatch), and cleaning up `requirements.txt.check`/`.body` scratch files on both
    failure paths (previously only cleaned up on success).
  - [x] All 6 Step 3 red tests now green (`tests/test_ci_check_lock_job.py`,
    `tests/test_makefile_check_lock_retry.py`); `make check-lock` verified green locally
    against current `dev` HEAD with real `uv 0.11.31`; full `tests/test_makefile.py` suite
    (62 tests) still green.
- [x] **STEP 5: Code Cleanup**
  - `make lint` and targeted `flake8` on touched test files: 0 issues.
  - Full targeted test run (`tests/test_ci_check_lock_job.py`,
    `tests/test_makefile_check_lock_retry.py`, `tests/test_makefile.py`): 62 passed, 1
    deselected (slow).
  - No unused imports/variables, commented-out code, debug prints, dead code, merge
    conflicts, or over-length lines found in files touched by this task.
  - Report: `ai-tasks/PYPOST-984/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - N/A for structured app logging/metrics (Prometheus/Grafana/log aggregation) — this task
    hardens a one-shot CI/build gate (`make check-lock`), not a long-running service; no
    consumer exists for such integrations.
  - Documented the distinct `stderr` messages added in Step 4 (`Makefile:54-55` compile-failure,
    `Makefile:59-60` per-attempt retry warning, `Makefile:68-69` genuine-drift message) as the
    CI-appropriate operator-facing observability equivalent, already covered by
    `tests/test_makefile_check_lock_retry.py`.
  - Report: `ai-tasks/PYPOST-984/50-observability.md`.
- [x] **STEP 7: Review and Technical Debt**
  - Follow-ups deferred from this task's DoD (production `check-lock` only): pinning `uv` on
    `check-lock-dev` (High), porting the retry/diagnostics/cleanup pattern to
    `check-lock-dev`/`check-lock-otel` (Medium), adding a `check-lock-otel` CI job (Low,
    pre-existing from PYPOST-787/927), and folding `check-lock` into `make check` (Low,
    pre-existing from PYPOST-927).
  - Report: `ai-tasks/PYPOST-984/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/setup.md` § "Dependency lock file (PYPOST-779)": added the retry/backoff behavior
    (up to 3 attempts, 1s/2s backoff), the two distinct `stderr` messages (compile-failure vs.
    genuine-drift), and the scratch-file cleanup guarantee for `make check-lock` (PYPOST-984,
    change 2); the `uv` version-pin cross-reference (change 1) was already added in Step 4.
  - `doc/dev/testing.md` § "CI lock verification (PYPOST-804, PYPOST-927)": updated the
    `check-lock` job description to note the pinned `uv` version (unlike sibling
    `check-lock-dev`) and the retry-before-fail behavior, keeping it consistent with the
    updated `setup.md` section.
  - Grepped `doc/` for `check-lock`: only `setup.md` and `testing.md` reference it; both now
    reflect the PYPOST-984 changes.
  - Report: `ai-tasks/PYPOST-984/70-dev-docs.md`.

## Language

- **Programming language**: Python (existing `pypost` codebase; fix lives in CI workflow YAML
  and/or the Python-driven `Makefile`/`scripts/` tooling — no new runtime language introduced).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-984/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-984/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-984/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-984/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-984/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/setup.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-984/70-dev-docs.md`

## Suggested branch name

`fix/PYPOST-984-check-lock-uv-pin-retry`
