# Roadmap: PYPOST-1197

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1197/10-requirements.md`
  - Language: Python
  - Business goal: ensure complete teardown of worker process hierarchy on timeout, eliminating orphaned background/child processes that leak resources or destabilize subsequent tests/CI
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1197/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_run_parallel_tests.py::test_worker_timeout_terminates_grandchild_process_group`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Implement `kill_process_group` with POSIX process group signaling and win32 fallback in `scripts/run_parallel_tests.py`
  - [x] Iteration 2: Update `SubprocessTestExecutor.run_test_file` to use `subprocess.Popen` with `start_new_session=True` on POSIX and invoke `kill_process_group` on worker timeout
  - [x] Iteration 3: Update and add tests in `tests/test_run_parallel_tests.py` verifying process group teardown on timeout, repro test passing, and `kill_process_group` unit tests
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1197/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1197/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1197/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/parallel_test_runner.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1197/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1197/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1197/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1197/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1197/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/parallel_test_runner.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
