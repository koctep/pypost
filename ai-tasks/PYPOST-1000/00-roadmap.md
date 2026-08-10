# Roadmap: PYPOST-1000

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_env_presenter.py::TestEnvPresenter.test_open_env_manager_passes_working_read_import_file`
    — locking test for EnvPresenter → EnvironmentDialog `read_import_file`
    wiring; was green against current production (coverage gap closed; no
    product defect found).
- [x] **STEP 4: Development**
  - [x] Confirmed Step 3 locking test green — no production change required.
    Presenter already passes
    `lambda path: load_import_candidates(path, self._storage)` into
    `EnvironmentDialog`. Test uses `ImportFakeStorage(FakeStorageManager)`
    with working `deserialize_environment_records` for plaintext records.
  - [x] Targeted pytest:
    `test_open_env_manager_passes_working_read_import_file` → 1 passed.
- [x] **STEP 5: Code Cleanup**
  - flake8 on `pypost/` clean via `make lint`; test-file E402 pattern
    pre-existing; no new line > 100 chars.
  - Full `tests/test_env_presenter.py` → 48 passed.
  - Report: `ai-tasks/PYPOST-1000/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - N/A — test-only; existing env-manager / import logs unchanged.
  - Report: `ai-tasks/PYPOST-1000/50-observability.md`.
- [x] **STEP 7: Review and Technical Debt**
  - No blockers; optional FakeStorageManager deserialize helper listed for
    orchestrator (no Jira link).
  - Report: `ai-tasks/PYPOST-1000/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/environments_dialog.md` Import Tests note for
    PYPOST-1000 presenter wiring lock.
  - Summary: `ai-tasks/PYPOST-1000/70-dev-docs.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (verification/testing debt within the existing Python codebase; no new
language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1000/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1000/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1000/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1000/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1000/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Suggested branch

`test/PYPOST-1000-envpresenter-read-import-file-wiring`

## Blocker review

**SAFE TO CLOSE** — optional FakeStorageManager deserialize default is
NON-BLOCKER follow-up only.
