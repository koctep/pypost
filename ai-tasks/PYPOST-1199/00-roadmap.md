# Roadmap: PYPOST-1199

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1199/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1199/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_run_parallel_tests.py::test_get_worker_timeout_precedence`
  - [x] `tests/test_run_parallel_tests.py::test_get_worker_timeout_invalid_cli_fallthrough`
  - [x] `tests/test_run_parallel_tests.py::test_get_worker_timeout_invalid_env_fallthrough`
  - [x] `tests/test_cli_parser_worker_timeout_flags`
  - [x] `tests/test_makefile_recipes.py::test_makefile_worker_timeout_contract`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Verified unit tests for get_worker_timeout precedence hierarchy (CLI > WORKER_TIMEOUT > default 30.0s) in tests/test_run_parallel_tests.py
  - [x] Iteration 2: Verified unit tests for invalid CLI timeout fallthrough (non-positive <= 0 values) in tests/test_run_parallel_tests.py
  - [x] Iteration 3: Verified unit tests for invalid WORKER_TIMEOUT environment variable fallthrough (empty, whitespace, non-numeric, zero, negative) in tests/test_run_parallel_tests.py
  - [x] Iteration 4: Verified CLIParser handling of --worker-timeout flags (space-separated, equals-separated, and missing value fallthrough) in tests/test_run_parallel_tests.py
  - [x] Iteration 5: Verified Makefile recipe contract for WORKER_TIMEOUT ?= 120 default and forwarding in test and test-cov in tests/test_makefile_recipes.py
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1199/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1199/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1199/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [/] `doc/dev/parallel_test_runner.md` — added `get_worker_timeout()` API & validation rules section, test coverage table (PYPOST-1199), and PYPOST-1199 references
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1199/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1199/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1199/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1199/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1199/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/parallel_test_runner.md` (updated: `get_worker_timeout()` API & validation rules, test coverage, references)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
