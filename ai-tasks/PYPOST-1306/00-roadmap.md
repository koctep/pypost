# Roadmap: PYPOST-1306

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Documented requirements for deterministic process-group termination test execution.
  - Artifact: `ai-tasks/PYPOST-1306/10-requirements.md`.
  - Business reason: eliminate flaky test failures under parallel load so CI and developers
    receive trustworthy regression feedback without false positives.
  - Outlined acceptance criteria, functional and non-functional requirements, and core entities.
  - Preserved robust process-group termination semantics and explicit bounded timeouts.
  - Requirements complete for independent review; STEP 1 remains in progress until acceptance.
- [x] **STEP 2: High-Level Architecture Design**
  - Designed architecture for deterministic grandchild process-group timeout verification.
  - Artifact: `ai-tasks/PYPOST-1306/20-architecture.md`.
  - Expanded worker timeout budget (3s-4s) providing headroom over pytest startup latency
    under heavy parallel load while staying safely within the 15s test timeout budget.
  - Specified immediate filesystem synchronization for grandchild PID registration.
  - Formulated failing repro test design for Step 3 reproducing the race condition.
- [x] **STEP 3: Failing Repro Test**
  - Red repro test:
    `tests/test_pypost_1306_failing_repro.py`
    `::test_starved_worker_timeout_reproduces_premature_pid_failure`
  - Reproduces triage failure deterministically under starved worker timeout
    (`--worker-timeout=0.2`).
  - Verifies deterministic process-group termination under sufficient budget
    (`--worker-timeout=3.0`).
- [x] **STEP 4: Development**
  - [x] Updated `tests/test_run_parallel_tests.py`: increased `--worker-timeout=1` to
    `--worker-timeout=3` in `test_worker_timeout_terminates_grandchild_process_group` to ensure
    adequate headroom against pytest startup latency under heavy CPU and parallel load.
  - [x] Verified durable and immediate writing of grandchild PID file prior to worker timeout.
  - [x] Validated via Make quality targets: single-worker and full test suites pass cleanly
    (`make test WORKERS=1 PYTEST_ARGS=...`, `make test PYTEST_ARGS=...`, `make lint`).
- [x] **STEP 5: Code Cleanup**
  - Linting and static analysis checks via Make targets (`make lint`, `make typecheck`).
  - Verified formatting, line lengths (<= 100 chars), and dead code / imports.
  - Targeted and regression testing via Make test runner.
  - Artifact: `ai-tasks/PYPOST-1306/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Analyzed observability for test execution and worker timeout diagnostics.
  - Documented structured logging events (`worker_timeout`, `parallel_test_run_completed`).
  - Documented test diagnostics and grandchild process verification error reporting.
  - Runtime/production service metrics documented as N/A for test runner infrastructure.
  - Artifact: `ai-tasks/PYPOST-1306/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts taken, code quality, test coverage, and performance.
  - Documented that expanded worker timeout directly addresses CPU starvation without crutches.
  - Verified clean syntax, PEP 8 formatting, explicit timeouts, and full test suite passes.
  - Documented that all other Sprint 2026 tasks are resolved and zero open tasks remain.
  - Artifact: `ai-tasks/PYPOST-1306/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Documented worker timeout budget guidelines for test-runner process-group tests
    (`test_worker_timeout_terminates_grandchild_process_group` in
    `tests/test_run_parallel_tests.py`) in `doc/dev/testing.md`.
  - Explained that worker timeouts must provide sufficient headroom (e.g. 3.0s) to account
    for pytest discovery and interpreter startup latency under parallel CPU load, ensuring child
    processes have ample time to spawn grandchild processes and record PIDs before the worker
    timeout triggers.
  - Added PYPOST-1306 reference and link.
  - Cross-referenced with `doc/dev/parallel_test_runner.md`.
  - Artifact: `doc/dev/testing.md`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1306/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1306/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1306_failing_repro.py`

### STEP 4: Development

- `tests/test_run_parallel_tests.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1306/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1306/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1306/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `doc/dev/parallel_test_runner.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
