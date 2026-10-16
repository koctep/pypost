# PYPOST-1413: Makefile test suites fail with shared venv materialization timeout under load

## Goals

PyPost relies on automated developer quality gates (`make check`, `make test`, `make test-cov`) and isolated continuous integration testing to guarantee code stability, prevent regressions, and ensure that changes can be merged safely and rapidly.

A critical pillar of test reliability is the Makefile integration test suite, which verifies that repository orchestration targets—such as environment initialization, dependency installation, idempotency stamps, and test execution—behave correctly in cleanly isolated workspaces. To run these tests without incurring the overhead of creating and populating full virtual environments from scratch for every individual test case, test fixtures utilize pre-warmed test environment materialization.

Under parallel execution (such as the default 8-worker parallel test runner) and under elevated system load, workspace preparation frequently times out during environment materialization. This causes widespread, intermittent test failures across multiple Makefile test suites, including:
- `tests/test_makefile_target_install_test.py`
- `tests/test_makefile_stamp_otel_idempotency.py`
- `tests/test_makefile_exit_behavior.py`
- `tests/test_makefile_install_stamp_contract.py`
- `tests/test_makefile_stamp_test_idempotency.py`
- `tests/test_makefile_markers.py`
- `tests/test_makefile_recipes.py`
- `tests/test_makefile_target_filtering.py`

This instability introduces severe business and workflow friction:
1. **Developer Velocity Roadblock**: Engineers cannot rely on `make test` or `make check` locally because test runs randomly fail due to environment preparation timeouts rather than actual code regressions.
2. **CI Pipeline Flakiness**: Shared CI runners operate under variable CPU and disk I/O contention. When test runs hit false-positive timeouts, builds fail, PR reviews stall, and developers are forced to re-run pipelines repeatedly.
3. **Erosion of Trust in Automated Gates**: When quality gate failures are dominated by test infrastructure timeouts instead of real defects, team members lose confidence in test results, increasing the risk that true regressions slip into the codebase unnoticed.

The primary goal of this task is to establish resilient, fast, bounded, and deterministic workspace preparation for Makefile test suites. Test environment materialization must execute within predictable resource budgets and withstand parallel execution and high load without false-positive timeout failures, while preserving strict workspace isolation.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **Software Engineer**, I want local Makefile test suites (`make test`) to run reliably and quickly without timing out during environment setup, so that I can validate my changes with confidence before pushing code.
- As a **CI/CD Engineer**, I want automated test runs executing on concurrent workers under heavy I/O and CPU contention to consistently complete within budgeted operational limits, so that build pipelines remain stable, green, and non-flaky.
- As a **Quality Assurance Engineer**, I want test workspaces to remain strictly isolated from one another without cross-contamination or race conditions during parallel preparation, so that test outcomes are 100% reproducible and deterministic.
- As a **Release Manager**, I want the repository quality gate (`make check`) to pass consistently on all development machines and CI agents, so that releases and deployments are never delayed by environmental test harness timeouts.

## Definition of Done

This task is considered complete when:
1. All affected Makefile integration test suites pass reliably without timeout failures under both single-worker and 8-worker parallel test execution (`make test` and `make check`):
   - `tests/test_makefile_target_install_test.py`
   - `tests/test_makefile_stamp_otel_idempotency.py`
   - `tests/test_makefile_exit_behavior.py`
   - `tests/test_makefile_install_stamp_contract.py`
   - `tests/test_makefile_stamp_test_idempotency.py`
   - `tests/test_makefile_markers.py`
   - `tests/test_makefile_recipes.py`
   - `tests/test_makefile_target_filtering.py`
2. Workspace environment materialization overhead is significantly reduced, ensuring that individual workspace preparation times operate comfortably within established operational timeouts even under high concurrent I/O load.
3. Strict test workspace isolation is preserved: changes, file mutations, or stamp manipulations performed in one test workspace cannot affect concurrent or subsequent test cases.
4. Concurrency handling during shared pre-warmed base environment bootstrap and materialization is robust: lock acquisition, preparation, and publication cleanly prevent race conditions, stale locks, and partial state reads.
5. In the event of an unavoidable timeout or cancellation, process cleanup budgets and error recovery prevent orphaned background processes or corrupted workspace directories from wedging subsequent test runs.
6. The entire repository quality gate (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) passes cleanly.

## Task Description

### Problem Statement

During test suite execution, tests that exercise Makefile targets require clean, isolated project workspaces with an active virtual environment containing basic test dependencies (`pytest`, `flake8`). To optimize runtime, the test framework bootstraps a shared pre-warmed base environment in a temporary location and materializes copies of this environment into each test workspace.

However, the current materialization procedure incurs heavy I/O latency (taking ~15.6 seconds even with zero load on an idle system). When tests are executed in parallel across multiple workers (e.g., 8 workers scheduled by `scripts/run_parallel_tests.py`), concurrent I/O contention causes workspace materialization to exceed the rigid 20-second preparation timeout. As a result, tests abort with `RuntimeError: shared venv materialization failed: ... Command '['...']' timed out after 20 seconds`, cascading across dozens of test cases.

### Scope

- **In-Scope**:
  - Defining performance, timeout, and concurrency requirements for Makefile test workspace environment preparation and materialization.
  - Ensuring deterministic execution of all Makefile test suites across parallel workers and varied host system loads.
  - Ensuring failure resilience, cleanup bounds, and clear diagnostic reporting when environment preparation encounters unexpected conditions.
  - Preserving workspace isolation guarantees across test invocations.
- **Out-of-Scope**:
  - Altering the production application code (`pypost/`).
  - Redesigning repository-level dependency locking or packaging standards defined in `Makefile`.
  - Changing the host hardware, operating system filesystem drivers, or external CI runner configurations.

### Functional Requirements

- **FR1 (Automated Workspace Environment Provisioning)**: Test suites requiring an isolated Makefile execution environment must have their workspace environment provisioned automatically upon fixture invocation without requiring manual developer setup.
- **FR2 (Strict Workspace Isolation)**: Each test case must execute against an independent, dedicated workspace. File creation, stamp modification, package installation, or directory cleanup within one workspace must not leak into or mutate any other test workspace.
- **FR3 (Concurrent Base Environment Bootstrap)**: When multiple test workers start simultaneously without an existing shared base environment, the bootstrap process must safely serialize initialization using non-blocking or bounded file locking. Exactly one worker must perform the bootstrap, while other workers wait boundedly and consume the published result once validated.
- **FR4 (Fast Materialization Under Load)**: Materializing the test environment into an individual test workspace must complete well below the preparation command timeout, even when multiple workers request materialization concurrently under high disk activity.
- **FR5 (Graceful Failure Recovery & Cleanup)**: If an environment preparation or materialization step fails or times out, all associated temporary resources and child processes must be terminated cleanly within a defined cleanup budget, leaving no zombie processes or corrupted partial directories.
- **FR6 (Cross-Suite Compatibility)**: All existing test contracts—including minimal workspace installations, full dependency slow-smoke suites, target filtering, stamp idempotency, and exit behavior tests—must remain fully compatible and functionally unmodified.

### Non-Functional Requirements

- **NFR1 (Performance & Timeouts)**:
  - Normal workspace materialization must complete in under 5 seconds under nominal conditions.
  - Under peak parallel load (8 concurrent workers), workspace materialization must not exceed 10 seconds, leaving an ample safety margin below the operational preparation timeout (20 seconds).
  - Base environment bootstrap (including creation, dependency installation, and validation) must remain strictly bounded by an explicit preparation budget.
- **NFR2 (Concurrency & Scalability)**:
  - The provisioning mechanism must support arbitrary worker counts (e.g., 1 to 16 workers) without encountering deadlocks, race conditions, or lock starvation.
  - Lock contention must be resolved with bounded polling and adaptive sleep intervals.
- **NFR3 (Determinism & Reliability)**:
  - 100% of test runs must pass without intermittent infrastructure-induced timeout failures across consecutive test suite runs.
- **NFR4 (Resource Hygiene)**:
  - File descriptors, temporary lock files, and child processes must be safely released upon test completion or abnormal termination.
  - Preparation subprocesses must be executed in isolated process groups to ensure complete termination upon timeout.

### Constraints and Assumptions

- **Makefile-Only Workflow**: All test operations, linting, and verifications must strictly follow repository rules and execute via `make` targets (`make test`, `make check`). Raw test runners must never be invoked directly.
- **POSIX Environment**: The test suite executes in a Linux/POSIX environment where filesystem operations (directory links, locks, permissions) operate under standard POSIX semantics.
- **Python Compatibility**: The solution must adhere to the project's supported Python version (`3.12+`).
- **Temporary Storage Constraints**: Workspaces are allocated in the system temporary directory (`/tmp` or `pytest` tmp_path). Cross-device boundaries between temporary storage locations and repository trees must be accommodated without unexpected filesystem failures.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Test Suite Run** | A scheduled execution of one or more test suites via `make test` | Run ID, worker count, target test files, start time, wall-clock duration, overall status |
| **Test Workspace** | An isolated directory sandbox configured for a specific test execution | Workspace directory path, active virtual environment path, configuration files, stamp markers |
| **Shared Base Environment** | A pre-warmed, validated virtual environment used as the template for test workspaces | Base directory path, Python interpreter version, installed core test dependencies (`pytest`, `flake8`), readiness marker |
| **Preparation Budget** | Bounded time allocation governing environment setup stages | Total preparation budget (seconds), lock acquisition timeout, command execution timeout, cleanup budget |
| **Parallel Test Worker** | An independent worker process executing a assigned batch of test files | Worker ID, assigned test files, current lifecycle state, error diagnostics |

### User Scenarios

#### Scenario 1: Parallel Test Suite Execution Under Load
A developer runs `make test` before submitting a pull request. The test runner schedules 8 concurrent worker processes executing dozens of test files in parallel. Multiple workers simultaneously request isolated workspaces for Makefile target tests. Each worker materializes its workspace environment swiftly within seconds without hitting the 20-second timeout. All test files execute concurrently and complete successfully.

#### Scenario 2: Cold Base Environment Initialization
A clean CI runner starts execution where no shared base environment exists in the temporary directory. Eight parallel workers launch simultaneously and compete to prepare their environments. One worker acquires the initialization lock and bootstraps the base environment, while the remaining seven workers wait boundedly on the lock. Once the base environment is validated and published, all workers proceed to materialize their workspaces rapidly without redundant installs or timeouts.

#### Scenario 3: Isolated Workspace Mutation and Idempotency Verification
A test verifies Makefile stamp idempotency by mutating `.venv` timestamps or simulating stale markers in its workspace. Because the workspace was materialized as an isolated instance, the mutations remain strictly confined to that test's workspace sandbox. The shared base environment and other concurrent test workspaces remain pristine and unaffected.

#### Scenario 4: Bounded Handling and Cleanup on Abrupt Interruption
During high system contention or unexpected system interruption, an environment command exceeds its allocated threshold. The harness immediately terminates the command and its entire process group within a strict cleanup budget (e.g., 1 second). Corrupted partial target directories are purged, preventing wedged state from causing cascading failures in subsequent tests.

## Q&A

**Q: Why do Makefile test suites need pre-warmed virtual environments instead of creating one on-demand in each test?**  
A: Creating a fresh virtual environment and running `pip install pytest flake8` takes 10 to 30 seconds per test. In a suite with dozens of Makefile tests, running full installation for every test would inflate test suite runtimes to tens of minutes. Pre-warming a shared template allows tests to run in seconds.

**Q: Why was the 20-second timeout failing if the operation took ~15.6 seconds on an idle system?**  
A: On an idle system, 15.6 seconds is already dangerously close to the 20-second threshold. In multi-worker parallel test runs (8 workers), concurrent disk operations compete for I/O bandwidth, easily causing the duration to exceed 20 seconds and triggering timeout aborts across the worker pool.

**Q: Why not simply increase the timeout to 60 or 120 seconds?**  
A: Increasing the timeout hides inefficient I/O operations and dramatically slows down test runs. If 8 parallel workers each stall for 60 seconds on disk I/O, the entire test suite becomes sluggish, degrading developer feedback loops and increasing CI costs. The requirement is for materialization to be fast and bounded, operating comfortably under 10 seconds even under load.

**Q: Does solving this issue require changing application production code in `pypost/`?**  
A: No. This task addresses test infrastructure reliability and workspace materialization within the test harness (`tests/makefile_test_helpers.py` and test suite execution). Application code in `pypost/` is out of scope.
