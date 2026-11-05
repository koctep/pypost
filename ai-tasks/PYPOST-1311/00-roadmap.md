# Roadmap: PYPOST-1311

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1311/00-roadmap.md`
  - `ai-tasks/PYPOST-1311/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1311/20-architecture.md`
  - Test-only fence: `wait_storage_idle` + `teardown` before temp-dir exit
  - Step 3: durable cleanup repro with gated async load (not N/A)
- [x] **STEP 3: Failing Repro Test**
  - Red test: `tests/test_env_persistence_tempdir_cleanup_repro.py::test_tempdir_cleanup_survives_in_flight_encrypted_async_load`
  - Failure mode: `OSError: [Errno 39] Directory not empty` on `TemporaryDirectory.cleanup()` while gated encrypted async load still writes the temp workspace (no `wait_storage_idle` + `teardown` fence)
- [x] **STEP 4: Development**
  - [x] Iteration 1: applied release + `wait_storage_idle` + `teardown` fence in Step 3 repro before `TemporaryDirectory.cleanup()`; same idle-then-assert + `teardown` in `finally` for named e2e missing-key test
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1311/40-code-cleanup.md`
  - Import-order / leading-blank cleanup in `tests/test_env_persistence_e2e.py`
  - `make lint` OK; scoped tests 2/2 PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1311/50-observability.md`
  - N/A for new production logs/metrics (test-only fence); documented existing coverage (`environment_storage_async_load_dispatched`, gateway wait-idle, env_presenter lifecycle teardown + metrics)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1311/60-tech-debt.md`
  - Test-only fence debt analysis; no BLOCKER timeouts; Phase D owns Jira filing
- [x] **STEP 8: Dev Docs**
  - Update `doc/dev/presenter_teardown.md` — TemporaryDirectory fence for encrypted async EnvPresenter tests
  - Update `doc/dev/testing.md` — env-persistence e2e / repro cleanup contract (cross-link teardown)
  - Cross-link from `doc/dev/environment_storage_async.md`
  - Note addressed status + links on PYPOST-1311 baseline mention in `doc/dev/collection_import.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1311/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1311/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_env_persistence_tempdir_cleanup_repro.py::test_tempdir_cleanup_survives_in_flight_encrypted_async_load`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1311/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1311/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1311/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/presenter_teardown.md` — Encrypted EnvPresenter + TemporaryDirectory fence
- `doc/dev/testing.md` — Env persistence temp-dir fence (PYPOST-1311)
- `doc/dev/environment_storage_async.md` — cross-link to fence docs
- `doc/dev/collection_import.md` — baseline PYPOST-1311 note points at fence docs

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
