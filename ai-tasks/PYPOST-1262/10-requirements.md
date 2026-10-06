# PYPOST-1262: Resolve Makefile test suite execution timeouts under parallel load

## Goals

The PyPost engineering and CI workflow relies on automated quality gates (`make check`, `make test`)
to ensure system integrity, test correctness, and prevent regressions. Rapid, reliable, and
deterministic test execution is essential for engineer velocity and autonomous agent runs.

During full-suite parallel execution (`make test`), integration tests in
`tests/test_makefile_lifecycle.py` and `tests/test_makefile_targets.py` consistently fail due to
worker timeouts at 120 seconds (`exit_code=-9`, `SIGKILL`). Both test files execute multiple real
virtual environment creations and pip package installations in isolated temporary directories.
Because the parallel test orchestrator (`scripts/run_parallel_tests.py`) dispatches test workloads
at the file level, all tests within each file run sequentially on a single worker subprocess.
The cumulative runtime of the heavy tests packed into these files exceeds the 120-second worker
timeout threshold, causing the orchestrator to terminate the worker and fail the entire test run.

From a business perspective, these timeouts create major operational friction:
- **False Negative Gate Failures:** Pull request validations and CI pipelines fail spuriously.
- **Autonomous Agent Stoppages:** Autonomous workflows (such as `sprint-task-runner`) halt upon
  encountering pre-existing test timeouts, requiring developer triage and unblocking.
- **Obscured Regressions:** Legitimate bugs can hide behind flaky or failing test suite runs.
- **Erosion of Developer Confidence:** Unstable test gates diminish developer trust in CI.

The goal of this task is to ensure that all test cases currently located in
`tests/test_makefile_lifecycle.py` and `tests/test_makefile_targets.py` execute reliably to
completion within bounded worker timeouts under full-suite 8-worker parallel load, eliminating
timeout failures while preserving 100% of test coverage and assertions.

## Programming Language

Python. Workflow documentation and task artifacts use English Markdown.

## User Stories

- As a **PyPost Developer / Autonomous Agent**, I want `make test` and `make check` to run to
  completion without timing out on Makefile lifecycle and target tests, so that my pull requests
  and development iterations can be validated quickly and reliably.
- As a **CI / Release Engineer**, I want every test file in the test suite to execute well under
  the 120-second worker timeout limit under multi-core parallel load, providing at least a 2x
  operating safety margin against system contention.
- As a **Quality Guardian**, I want all existing test assertions covering virtual environment
  creation, marker lifecycle, stamp idempotency, and Makefile target execution to remain fully
  enforced without skipping, removing, or weakening any assertions.
- As a **Test Suite Maintainer**, I want test files to follow repository modularity conventions,
  explicit bounded timeouts, and strict code formatting standards (line length <= 100).

## Definition of Done

This task is considered done when all the following acceptance criteria are met:

1. **AC-1 (Parallel Worker Timeout Elimination):** Full-suite parallel test runs (`make test`)
   execute all Makefile lifecycle and target tests without any worker timeout failures
   (`TIMED_OUT`, `exit_code=-9`).
2. **AC-2 (Test Coverage Preservation):** Every test case currently existing in
   `tests/test_makefile_lifecycle.py` (13 tests) and `tests/test_makefile_targets.py` (11 tests)
   continues to exist and execute with all assertions intact. No test may be removed or disabled.
3. **AC-3 (Target Execution Margin):** Every individual test file containing Makefile integration
   tests completes within a safe execution window (targeting < 60 seconds per worker file under
   8-worker parallel execution), providing a >= 2x margin relative to the 120s worker timeout.
4. **AC-4 (Standalone Execution Parity):** All Makefile test files pass cleanly when executed
   individually (e.g. `make test PYTEST_ARGS="tests/<test_file>.py"`).
5. **AC-5 (Backward Compatibility & Budget Enforcement):** All existing Makefile targets,
   regression checks in `tests/test_makefile_parallel_budget.py`, and test discovery mechanisms
   continue to function cleanly without regression.
6. **AC-6 (Quality Gate Cleanliness):** All repository quality checks (`make check`, `make lint`,
   `make typecheck`, `make verify-ai-tasks`) pass cleanly without errors or warnings.

## Task Description

### Problem Statement

During full-suite parallel testing (`make test`), the parallel test runner executes tests across
concurrent worker subprocesses (defaulting to 8 workers). Two Makefile integration test files
consistently exceed the fixed 120-second worker timeout:

1. **`tests/test_makefile_lifecycle.py` (13 tests):**
   - Contains `TestMarkerLifecycle` (3 tests), `TestVenvExtraStampIdempotency` (8 tests), and
     `TestInstallExtraStampContract` (2 tests).
   - In standalone execution, the 3 tests in `TestMarkerLifecycle` alone require ~99.6 seconds
     (~31.9s, ~35.7s, ~31.9s) because each test builds real virtual environments (`make venv`).
   - The remaining 10 tests require ~15-25 seconds each.
   - Total cumulative runtime exceeds 300 seconds. A worker running the file times out and is
     killed at 120.0s during the 4th test (`test_venv_test_skips_pip_when_current`).

2. **`tests/test_makefile_targets.py` (11 tests):**
   - Contains `TestExitBehavior` (3 tests) and `TestTargetExecution` (8 tests).
   - Tests in `TestTargetExecution` perform full `make install` (`.[dev,otel]`) and invoke nested
     `make test` or `make lint` targets in fresh temporary workspaces.
   - For example, `test_lint_succeeds_from_bare_venv_via_venv_test` takes ~58.3 seconds and
     `test_venv_test_installs_pytest_and_flake8` takes ~58.3 seconds.
   - Total cumulative runtime exceeds 300 seconds. A worker running the file times out and is
     killed at 120.0s during the 5th test (`test_make_test_excludes_slow_marker`).

3. **Related Contention in `tests/test_pytest_exit_policy.py`:**
   - As noted during PYPOST-1285 triage, tests invoking nested `make install` and `make test`
     also experience heavy cumulative durations when executed concurrently.

### Root Cause Analysis

The root cause of these timeouts is a structural mismatch between the runner's concurrency model
and the workload density of the test files:

1. **File-Level Dispatch Concurrency:**
   The parallel orchestrator (`scripts/run_parallel_tests.py`) dispatches work at file-level
   granularity (`DispatchUnit`). It groups all tests within a given `.py` file into a single
   execution unit executed sequentially in one subprocess under a fixed `--worker-timeout` (120s).

2. **Expensive Real Environment Lifecycle Operations:**
   Each test utilizing the `make_workspace` fixture creates an isolated temporary directory, runs
   `make venv` (`python3 -m venv`, `ensurepip --upgrade`, `pip install --upgrade pip`), and
   subsequently runs `pip install -e ".[dev]"` or `.[dev,otel]`. These disk- and network-isolated
   wheel installations take 15 to 60 seconds per test case.

3. **High Test Density per File:**
   Grouping 13 heavy lifecycle tests into `test_makefile_lifecycle.py` and 11 heavy target execution
   tests into `test_makefile_targets.py` creates sequential workloads of 300+ seconds per file.

4. **Resource Contention under Parallel Load:**
   When 8 parallel workers run concurrently, CPU and disk I/O contention significantly slows down
   venv initialization, file copying, and pip wheel extraction. Operations that take 20s in
   isolation take 30-50s under contention, guaranteeing worker timeout termination.

### Scope Boundaries

#### In Scope

- Restructuring and decomposing `tests/test_makefile_lifecycle.py` and
  `tests/test_makefile_targets.py` so that no single test file contains an excessive cumulative
  workload of heavy virtual environment operations.
- Evaluating optimization and modularization strategies (such as splitting test classes into
  dedicated test files, grouping scenarios, or caching fixture workspaces).
- Preserving all existing test cases, verifications, and assertions.
- Maintaining test discovery conventions (`tests/test_*.py`) and test timeout marker rules.
- Updating test suite budget regression checks in `tests/test_makefile_parallel_budget.py` to
  reflect any modularized test suite structure.

#### Out of Scope (Non-Goals)

- Modifying core application production logic in `pypost/`.
- Deleting, skipping, or weakening any existing test case or assertion.
- Increasing the global `WORKER_TIMEOUT` beyond 120s as a blanket bypass.
- Modifying Makefile recipe semantics outside test stability and execution requirements.

## Functional Requirements

- **FR-1 (Worker Completion Within Timeout):** Every test file in the test suite must reliably
  complete within the 120-second worker timeout limit under full-suite parallel execution
  (`make test` with 8 workers).
- **FR-2 (Workload Decomposition & Modularity):** Heavy test classes and test scenarios currently
  concentrated in `test_makefile_lifecycle.py` and `test_makefile_targets.py` must be split or
  restructured across granular test files (e.g. per test class or logical scenario) so that the
  cumulative execution time per file remains safely bounded.
- **FR-3 (Full Coverage Preservation):** Every test case and assertion across all 13 tests of
  `test_makefile_lifecycle.py` and 11 tests of `test_makefile_targets.py` must continue to exist,
  execute, and validate the exact same behaviors.
- **FR-4 (Explicit Test Timeouts):** Every test file and test method must declare bounded timeouts
  (`pytestmark = pytest.mark.timeout(...)` and/or method-level marks) complying with repository
  standards (`do-testing` and `lsr-python`).
- **FR-5 (Test Discovery Compatibility):** All decomposed test files must follow standard naming
  conventions (`tests/test_*.py`) and be automatically discoverable by `make test`, `make test-cov`,
  and `scripts/run_parallel_tests.py`.
- **FR-6 (Budget Check Alignment):** Regression checks in `tests/test_makefile_parallel_budget.py`
  must be maintained and updated to validate the restructured suite structure and bounded timeout
  budgets.

## Non-Functional Requirements

- **NFR-1 — Execution Safety Margin:** Under full-suite 8-worker parallel load, each test file
  must complete in <= 60 seconds, ensuring at least a 2x safety margin against the 120s timeout.
- **NFR-2 — Hermetic Workspace Isolation:** Tests must continue to run in isolated temporary
  workspaces without shared mutable state or concurrency hazards between workers.
- **NFR-3 — Formatting & Line Length:** All created or modified files must strictly comply with
  repository line length limits (all lines <= 100 characters).
- **NFR-4 — Clean Quality Gates:** The repository must pass `make check` (`make lint`, `make test`,
  `make verify-ai-tasks`) and `make typecheck` with zero errors.

## Main Entities and Interactions

- **Parallel Test Runner (`scripts/run_parallel_tests.py`):**
  Orchestrates test execution across worker processes, grouping tests by file and
  enforcing the 120s worker timeout.
- **Worker Subprocess:**
  Executes pytest sequentially on a single test file; terminated if exceeding timeout.
- **Split Test Files (`tests/test_makefile_*.py`):**
  Units of concurrent execution, each hosting a bounded subset of tests (< 60s runtime).
- **Test Fixture (`make_workspace`):**
  Provides a hermetic temporary workspace with Makefile, pyproject, and virtualenvs.
- **Parallel Budget Suite (`tests/test_makefile_parallel_budget.py`):**
  Guards timeout budgets, suite modularity, and file naming conventions.

## Constraints and Assumptions

- Makefile integration tests test real subprocess commands (`make venv`, `make install`, etc.)
  and cannot be entirely converted to pure mocks without losing end-to-end verification value.
- The parallel runner assigns entire test files to workers. Splitting tests into more test files
  directly distributes the workload across available parallel workers.
- Subprocess execution times vary depending on host hardware and CPU/disk contention. Solutions
  must provide ample headroom rather than operating on the edge of the timeout limit.
- All commands must be run via `make` targets per repository rules.

## Q&A

- **Q: Why not simply increase WORKER_TIMEOUT in Makefile from 120s to 300s?**
  **A:** Increasing the timeout masks performance bottlenecks, prolongs test suite execution, and
  delays detection of real deadlocks or infinite loops. Splitting tests across files parallelizes
  the workload across available CPU cores and reduces total wall-clock time.

- **Q: How many tests are in each problematic file currently?**
  **A:** `tests/test_makefile_lifecycle.py` contains 13 tests across 3 classes.
  `tests/test_makefile_targets.py` contains 11 tests across 2 classes.

- **Q: How will test coverage be verified after restructuring?**
  **A:** Step 4 verification will confirm that the total test count and individual test identifiers
  match the baseline inventory, and that all assertions continue to execute and pass.

- **Q: What is the target runtime for each split test file?**
  **A:** Under parallel load with 8 workers, each file should complete in under 60 seconds,
  providing a 2x safety margin against the 120-second worker timeout threshold.
