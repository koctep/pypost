# PYPOST-1234: Resolve test execution timeouts under full-suite parallel load

## Goals

The PyPost engineering workflow relies on continuous automated testing (`make check`, `make test`)
to guarantee code quality and prevent regressions across the codebase. Rapid, deterministic test
feedback is essential for developer velocity and autonomous agent workflows.

During full-suite parallel execution, tests in `tests/test_makefile.py` and
`tests/test_pytest_exit_policy.py` encounter worker and subprocess timeouts due to system resource
contention (CPU and I/O pressure). Because the standalone duration of `tests/test_makefile.py`
(~109 seconds) is already close to the standard worker timeout limit (120 seconds), concurrent
execution across parallel workers causes the total duration to exceed the threshold, triggering
worker termination and failing the test gate. Similarly, internal subprocess timeouts within
`tests/test_pytest_exit_policy.py` fail under concurrent load when operations exceed their
budget.

From a business perspective, flaky test failures and machine-load-dependent timeouts create major
blockers:
- They cause false negative quality gate failures in CI and local environments.
- They halt autonomous AI agent pipelines and require manual engineer triage.
- They obscure real regressions behind transient timeout noise.
- They degrade developer trust in the automated test suite.

The goal of this task is to ensure that all Makefile integration tests and exit-policy regression
tests execute reliably and deterministically within bounded execution limits under realistic
parallel test execution, eliminating load-induced timeout flakes while fully preserving test
coverage and verification rigor.

## Programming Language

Python. Task documentation and workflow artifacts use English Markdown.

## User Stories

- As a **PyPost Contributor / Agent**, I want `make test` and `make check` to run deterministically
  to completion under parallel execution without failing due to worker timeouts or subprocess
  deadlines, so that I can validate changes efficiently without false negative blockers.
- As a **CI / Release Engineer**, I want each test suite component to operate with sufficient
  execution margin (at least 2x expected execution time under load) relative to its timeout limit,
  so that fluctuations in system load do not trigger pipeline failures.
- As a **Quality Guardian**, I want all existing Makefile lifecycle checks, virtual environment
  creation verifications, and exit code policy assertions to remain fully enforced, ensuring that
  test speed or reliability improvements do not degrade test coverage.
- As a **Test Suite Maintainer**, I want heavy test suites to adhere to project standards
  (`do-testing`) with explicit, bounded timeouts and no unbounded waits or silent hanging behavior.

## Definition of Done

This task is considered done when all the following acceptance criteria are met:

1. **AC-1 (Makefile Integration Parallel Stability):** All Makefile integration tests execute
   successfully during full-suite parallel runs (`make test`) without triggering worker timeout
   terminations or hanging workers.
2. **AC-2 (Exit Policy Subprocess Stability):** Subprocess-based tests in
   `tests/test_pytest_exit_policy.py` (specifically
   `test_make_test_fails_with_exit_code_5_when_no_tests_collected`) execute to completion without
   `subprocess.TimeoutExpired` errors during full-suite parallel runs under concurrent system load.
3. **AC-3 (Test Coverage Preservation):** All 65 tests in `tests/test_makefile.py` and all tests
   in `tests/test_pytest_exit_policy.py` (or their organized equivalents) continue to run and assert
   their full set of behavioral requirements. No tests may be skipped, silenced, or deleted.
4. **AC-4 (Standalone Execution Fidelity):** All modified or restructured test suites pass cleanly
   when run in standalone mode (e.g. `make test PYTEST_ARGS="..."`).
5. **AC-5 (Adequate Runtime Margin):** The execution duration of any individual worker unit under
   parallel load provides a safe operating margin against configured worker timeout thresholds,
   preventing edge-of-timeout flakiness.
6. **AC-6 (Quality Gate Cleanliness):** Standard quality gates (`make lint`, `make typecheck`,
   and `make verify-ai-tasks`) pass cleanly without errors or warnings.

## Task Description

### Problem Statement

During full-suite parallel test runs (`make test`), the test runner executes test files concurrently
across multiple worker processes. Two related timeout failures occur under full-suite load:

1. **`tests/test_makefile.py` Worker Timeout:**
   The entire test file `tests/test_makefile.py` (952 lines, 65 tests) is executed by a single
   worker process. In standalone execution, the file requires approximately 109 seconds. When run
   concurrently with the rest of the test suite, CPU and disk contention slows execution past the
   120-second worker timeout limit (`WORKER_TIMEOUT=120`). The test orchestrator terminates the
   worker process before individual test results are collected, causing a whole-file failure.

2. **`tests/test_pytest_exit_policy.py` Internal Subprocess Timeout:**
   In `test_make_test_fails_with_exit_code_5_when_no_tests_collected`, an internal `make install`
   invocation specifies a 25-second subprocess timeout. Under the CPU contention of a parallel test
   run, package installation and virtual environment validation can exceed 25 seconds, raising
   `subprocess.TimeoutExpired`.

Both failures belong to the same cluster of issues: integration tests that invoke subprocesses
running into fixed time boundaries when competing for CPU and I/O resources during parallel suite
execution.

### Business Value & Impact

Resolving these timeout issues directly impacts developer productivity and engineering velocity:
- **Zero False-Positive Quality Gates:** Enables clean `make check` and `make test` runs that
  accurately reflect repository health.
- **Unblocked AI Agent Workflows:** Allows autonomous pipelines (such as `sprint-task-runner`) to
  complete without needing manual intervention for known baseline test failures.
- **Predictable CI Runtime:** Stabilizes CI durations and prevents costly rebuild retries caused by
  transient timeouts.

### Scope Boundaries

#### In Scope

- Ensuring the Makefile test suite completes within safe timeout limits under both standalone and
  parallel suite load.
- Ensuring the pytest exit policy test subprocess calls complete reliably under parallel suite load.
- Verifying stability through repeated parallel test runs under simulated or real load.
- Maintaining compliance with repository testing standards (`do-testing`), including explicit
  per-test bounded timeouts.
- Updating developer documentation if runner contracts or test execution guidelines are affected.

#### Out of Scope (Non-Goals)

- Modifying core application runtime logic under `pypost/`.
- Deleting, disabling, or marking tests as xfail or skip to bypass timeout limits.
- Removing worker timeouts or global test timeouts from the parallel test runner.
- Changing Makefile target contracts or functional behavior outside test stability needs.

## Functional Requirements

- **FR-1 (Parallel Worker Completion):** The test execution orchestrator must be able to run all
  Makefile tests to completion without any worker exceeding the maximum worker timeout limit during
  a full test suite run.
- **FR-2 (Subprocess Contention Tolerance):** Test cases that execute subprocess invocations (such as
  `make install` or `make test` within temporary test workspaces) must have timeout budgets
  configured to tolerate realistic parallel execution contention without timing out.
- **FR-3 (Behavioral Verification Invariance):** All functional checks verified by the Makefile
  suite (including virtual environment initialization, marker lifecycle, dependency
  synchronization, target prerequisites, license inventory, and MCP fixture targets) must remain
  asserted and verified.
- **FR-4 (Exit Policy Invariance):** The exit policy test suite must continue to verify that
  `make test` properly detects and propagates pytest exit code 5 (no tests collected) as a build
  failure.
- **FR-5 (Deterministic Execution):** Test outcomes must not fluctuate between success and failure
  across repeated runs on identical codebases under normal multi-core system loads.

## Non-Functional Requirements

- **NFR-1 — Execution Margin & Performance:** The execution time of each test worker must maintain a
  healthy safety margin below its allocated timeout, avoiding "cliff-edge" execution times.
  Overall test suite wall-clock duration must remain efficient.
- **NFR-2 — Boundedness & Fail-Safe Protection:** All tests and runner processes must maintain
  bounded execution limits per the `do-testing` skill, ensuring that deadlocks or infinite loops
  are cleanly aborted rather than hanging indefinitely.
- **NFR-3 — Hermetic Isolation:** Each test case or test worker must execute in isolated temporary
  workspaces without shared mutable state, avoiding race conditions or file locking conflicts when
  executed concurrently.
- **NFR-4 — Maintainability:** Test organization and configuration must be clear, well-structured,
  and documented so future maintainers understand how timeout budgets and test workloads are
  managed.

## Main Entities and Interactions

| Entity | Role in System | Interactions / Boundary Responsibilities |
| --- | --- | --- |
| Parallel Test Orchestrator | Execution Coordinator | Dispatches test workloads to workers, monitors health, and enforces worker timeout limits |
| Test Worker Process | Test Runner | Executes assigned test cases within an allocated worker process |
| Makefile Integration Suite | Quality Verification | Exercises real Makefile targets and lifecycle scripts in isolated workspaces |
| Exit Policy Test Suite | Quality Verification | Exercises pytest exit code propagation through Makefile invocations |
| Test Workspace | Isolation Boundary | Hermetic filesystem sandbox providing isolated virtual environments and project manifests |
| Quality Gate (`make test`) | Quality Enforcement | Aggregates individual test results across all workers into a consolidated pass/fail report |

## Constraints and Assumptions

- Tests in `tests/test_makefile.py` and `tests/test_pytest_exit_policy.py` test real shell invocations
  and virtual environment installations; they inherently perform disk I/O and process spawning.
- The standard machine environment runs multi-core Linux systems with varying CPU and disk
  performance characteristics.
- All operations must continue to conform strictly to repository standards (Make-only toolchain,
  PEP 8 / flake8, mypy typing, and `do-testing` timeout rules).

## Q&A

- **Q: Why is a test that passes in 109 seconds considered failing?**
  **A:** When a test file takes 109 seconds standalone against a 120-second timeout, its margin is
  less than 10%. Under the CPU and disk I/O contention of a full parallel suite run, runtime
  routinely increases by 20–50%, reliably exceeding the 120-second limit. A healthy test suite
  requires sufficient margin to prevent flakiness.

- **Q: Why are `test_makefile.py` and `test_pytest_exit_policy.py` addressed in the same ticket?**
  **A:** Both failures were identified during full-suite triage as part of the same root cause
  cluster: Makefile-invoking subprocess tests encountering timeout thresholds under concurrent CPU
  contention. Stabilizing the test suite requires addressing both instances.

- **Q: Does solving this require altering production application logic?**
  **A:** No. This issue is strictly within the test suite and test execution orchestration.
  Production source code under `pypost/` is unaffected.

- **Q: Why not just raise the global WORKER_TIMEOUT to a very high number (e.g. 600 seconds)?**
  **A:** While adjusting timeout thresholds is one design option, a single flat global timeout
  increase can delay detection of actual hangs or deadlocks across the entire test suite. The
  architectural evaluation in Step 2 will compare potential strategies (such as workload
  distribution, caching, or budgeting) to determine the best approach.
