# PYPOST-1148: Fix make check pytest deadlock on full test suite execution

## Goals

The PyPost engineering workflow depends on automated continuous integration gates (`make check`, `make test`) to validate code quality, guard against regressions across 2,700+ tests, and ensure release readiness. Currently, running the test suite in batch mode suffers from an indefinite deadlock/hang during execution around asynchronous collection import testing.

From a business and engineering perspective, this task is needed to:
1. **Restore CI Quality Gate Integrity**: Enable developers and automated CI pipelines to execute `make check` and `make test` reliably to completion without manual intervention or hung processes.
2. **Prevent CI Runner Blocking**: Eliminate indefinite thread/process deadlocks that consume CI compute resources and block deployment pipelines.
3. **Ensure Predictable and Deterministic Test Lifecycle**: Ensure that tests involving asynchronous operations, background processing, and UI event loops cleanly initialize, execute, and terminate within bounded time limits.

**Implementation language:** Python

## User Stories

- As a **developer**, I want the entire automated test suite to run reliably to completion via `make check` and `make test`, so that I can validate code changes and get quick, deterministic feedback without execution freezing indefinitely.
- As a **CI/CD engineer**, I want test suites running in batch mode to clean up all background threads and event loops, so that build pipelines do not experience unrecoverable deadlocks or hung runner agents.
- As a **release maintainer**, I want the test gate stabilization goal of the sprint achieved, so that pre-existing flakes and deadlocks do not block releases or obscure real defects.

## Definition of Done

1. **Deadlock-Free Batch Test Execution**:
   - Running the full fast test suite (`make test` / `make check`) passes reliably to completion without hanging or deadlocking.
   - The test suite completes deterministically in both single-test isolation and full batch runs of 2,700+ tests.

2. **Clean Lifecycle & Resource Teardown**:
   - All background threads, workers, and asynchronous event loops created during test execution terminate cleanly before the test finishes or during fixture teardown.
   - No lingering threads or unjoined workers remain that prevent process exit or cause subsequent tests to deadlock in futex waits.

3. **Enforced Timeouts and Fail-Safe Bounded Execution**:
   - Any test or background task execution is strictly bounded by deterministic timeouts, guaranteeing that execution cannot stall indefinitely.
   - If an unexpected stall occurs, it fails fast with diagnostic information rather than causing an unbounded hang.

4. **Quality Gates Pass**:
   - `make lint` passes without static analysis or formatting violations.
   - `make test` passes without deadlocks or regressions across the entire suite.
   - `make verify-ai-tasks` passes with all task artifacts intact.

## Task Description

### Problem

When running the full test suite in batch mode (e.g., `make check` / `pytest tests/ -m "not slow"`), pytest hangs indefinitely in a futex deadlock (specifically around `tests/test_collection_import_async_gaps.py::test_unexpected_reader_exception_surfaces_invalid_dialog`).
While the individual test passes in fraction-of-a-second isolation, running in batch mode with thousands of preceding and succeeding tests causes background threads or event loop teardown to deadlock without clean termination. Furthermore, standard signal-based timeouts fail to interrupt the futex wait state, causing the entire CI runner or developer session to freeze.

### Scope

**In scope:**
- Ensuring the asynchronous collection import test scenarios and related components cleanly manage worker and event loop lifecycles so test runs never deadlock.
- Establishing proper lifecycle teardown and bounded wait mechanisms to ensure complete termination of background workers.
- Verifying full test suite execution passes cleanly under `make test` and `make check`.

**Out of scope:**
- Modifying business functionality of collection import itself (import parsing formats, conflict handling algorithms, or UI presentation).
- Changes to unrelated test modules or unrelated background processes.
- Changes to the underlying CI infrastructure or pytest test runner binaries.

### Main Entities and Domain Interactions

- **Test Suite Runner**: Coordinates batch discovery and execution of tests, enforcing execution gates and timeouts.
- **Collection Import Workflow**: High-level domain workflow that prompts for import files, processes collections asynchronously off the main thread, and reports results or errors back to the interface.
- **Async Import Worker**: Domain entity executing collection parsing and file reading in the background to keep the interface responsive.
- **Event Loop & Thread Lifecycle Coordinator**: Domain mechanism responsible for orchestrating worker execution, joining threads, and ensuring graceful shutdown upon completion or error.

### Functional Requirements

1. **Graceful Error Handling and Teardown**:
   - When an unexpected error occurs during asynchronous collection import, all associated worker threads must be properly stopped and cleaned up.
   - The test harness and presenter must reliably await or enforce complete shutdown of asynchronous tasks before proceeding to teardown.

2. **Deterministic Completion**:
   - Tests exercising asynchronous collection import error conditions must complete deterministically regardless of test execution order or batch size.

3. **Isolated Test State**:
   - Background tasks initiated by a test must not outlive the test case or leak active threads into subsequent test executions.

### Non-Functional Requirements

- **Reliability & Determinism**: Test execution must never hang or deadlock, under any batch load or sequence.
- **Performance**: Teardown and worker cleanup must not introduce significant delays (overhead should be minimal, on the order of milliseconds).
- **Maintainability**: Clear and consistent lifecycle management patterns adhering to repository standards.

### Constraints and Assumptions

- All operations and validations must strictly be performed via repository `make` targets (`make check`, `make test`, `make lint`).
- The fix must preserve all existing test coverage and business error handling for collection import failures.

## Q&A

**Q: Why does the test pass in isolation but deadlock in the full suite?**
A: In isolation, process termination immediately follows the single test execution, masking unjoined threads or lingering event loop resources. In a full batch run of 2,700+ tests, lingering background workers or incompletely shut down event loops interact with subsequent tests and runtime teardown, triggering futex wait deadlocks.

**Q: Does this task change end-user collection import features?**
A: No. The user-facing behavior of collection import remains unchanged. The task ensures robust lifecycle management and cleanup so that test execution and asynchronous operations terminate deterministically.

**Q: Where is this tracked in Jira?**
A: [PYPOST-1148](https://pypost.atlassian.net/browse/PYPOST-1148) in the "CI Gate Stabilization" sprint backlog.
