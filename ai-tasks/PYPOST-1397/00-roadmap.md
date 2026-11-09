# Roadmap: PYPOST-1397

## Task Metadata

- **Implementation language**: Python
- **Jira**: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) — Debt (1 SP), Low
- **Sprint**: Test Gate Recovery

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Artifact: `ai-tasks/PYPOST-1397/10-requirements.md`
  - Business goal: restore deterministic `check-lock-dev` quality gate without
    weakening drift detection
- [x] **STEP 2: High-Level Architecture Design**
  - Artifact: `ai-tasks/PYPOST-1397/20-architecture.md`
  - Plan: regenerate committed `requirements-dev.txt` via `make lock-dev`; keep
    `check-lock-dev` contract unchanged
- [x] **STEP 3: Failing Repro Test**
  - [x] Existing red gate (no new test):
        `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
  - Confirmed RED via `make test` with targeted `PYTEST_ARGS` and via
    `make check-lock-dev` (stale message; exit 1 from Make target)
- [x] **STEP 4: Development**
  - [x] `Makefile` `lock-dev`: add `--upgrade` so regeneration matches fresh
        `check-lock-dev` resolve (uv otherwise keeps existing pins)
  - [x] Regenerated `requirements-dev.txt` with `make lock-dev` (uv 0.11.31)
  - [x] Confirmed `make check-lock-dev` green
  - [x] Confirmed Step 3 repro green via `make test`
- [x] **STEP 5: Code Cleanup**
  - Artifact: `ai-tasks/PYPOST-1397/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1397/50-observability.md` (N/A for new logs/metrics)
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1397/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/setup.md`: document `lock-dev --upgrade` rationale and
    PYPOST-1397 remediation when `check-lock-dev` reports stale lock
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1397/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1397/20-architecture.md`

### STEP 3: Failing Repro

- Existing red (no new test):
  `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
- Failure mode: `make check-lock-dev` reports
  `requirements-dev.txt is stale relative to requirements-dev.in`

### STEP 4: Development

- `requirements-dev.txt` (regenerated via `make lock-dev`)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1397/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1397/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1397/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/setup.md` (`lock-dev --upgrade` / stale-lock remediation; PYPOST-1397)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
