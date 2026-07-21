# Roadmap: PYPOST-877

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_env_presenter.py::TestEnvPresenter::test_async_load_wait_exits_near_deadline_when_never_complete`
- [x] **STEP 4: Development**
  - [x] Wired `test_async_load_refreshes_combo_when_encryption_enabled` and
        hang-exit proof to shared `tests.helpers.process_until.process_until`;
        removed timer-only `_async_load_wait` / unused `QEventLoop`/`QTimer`
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-877/40-code-cleanup.md`; lint clean; 45/45
        `tests/test_env_presenter.py` passed; no cleanup edits required
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-877/50-observability.md`; production logs/metrics N/A
        (test-harness-only `process_until` wire-up); failure signal is pytest
        `AssertionError` from shared helper + hang-exit proof
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-877/60-tech-debt.md`; verdict SAFE TO CLOSE;
        no blocker debt; optional TD-1 (slim hang subprocess proof);
        consumer list update deferred to Step 8; already-tracked
        PYPOST-828/829/830/886
- [x] **STEP 8: Dev Docs**
  - [x] `ai-tasks/PYPOST-877/70-dev-docs.md`;
        `doc/dev/gui_testing.md` consumer list + References;
        `doc/dev/environment_storage_async.md` cross-link

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-877/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-877/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_env_presenter.py::TestEnvPresenter::test_async_load_wait_exits_near_deadline_when_never_complete`
  (green after Step 4: shared `process_until` ends near wall-clock deadline)

### STEP 4: Development

- `tests/test_env_presenter.py` — wire async-load encryption refresh + hang
  proof to `tests.helpers.process_until.process_until`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-877/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-877/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-877/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-877/70-dev-docs.md`
- `doc/dev/gui_testing.md` — env-presenter on shared `process_until` consumer list
- `doc/dev/environment_storage_async.md` — async-load wait cross-link
