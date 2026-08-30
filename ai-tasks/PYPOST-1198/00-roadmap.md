# Roadmap: PYPOST-1198

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [ ] `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config` — extended with
    `assert any("worker_timeout=30.0" in message for message in messages)`; fails today (red)
    because `parallel_test_run_started` does not yet log `worker_timeout`.
- [x] **STEP 4: Development**
  - [x] Implemented `worker_timeout` field in the `parallel_test_run_started` log line: added
    `worker_timeout=%s` to the log format string and `config.worker_timeout` as its positional
    arg in `run_parallel_tests()` (`scripts/run_parallel_tests.py`), matching the `%s` float
    style used by the existing `worker_timeout` WARNING log. Makes
    `tests/test_run_parallel_tests.py::test_parallel_runner_logs_run_config` pass; full
    `tests/test_run_parallel_tests.py` suite (21 tests) passes.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/parallel_test_runner.md` (PYPOST-1192's own doc): the "Structured logs
    (timeout path)" section previously stated `parallel_test_run_started` does not include
    `worker_timeout=…`; corrected that one sentence to reflect that it now does (PYPOST-1198),
    pointing at the existing "Worker timeout precedence" section. No other content changed;
    the broader runner-contract doc gap noted in `60-tech-debt.md` (item "Runner contract docs
    deferred to Step 8") is pre-existing PYPOST-1192 debt and out of scope here.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1198/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1198/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1198/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1198/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1198/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
