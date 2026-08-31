# PYPOST-1197: Harden worker timeout with process-group kill

## Goals

Developers and continuous integration (CI) pipelines rely on the parallel test runner to execute test suites quickly, predictably, and cleanly. In PYPOST-1192, a wall-clock timeout was introduced to ensure the test orchestrator does not wait indefinitely for hung test workers.

However, terminating only the top-level worker process when a timeout occurs leaves behind any background threads, subprocesses, child helpers, or external tools (such as headless browser/UI helpers, mock servers, or child compilers) spawned by that worker during its run. These orphaned background processes continue executing indefinitely in the operating system, holding network ports, consuming memory and CPU, locking disk files, and corrupting shared test resources. This leads to flaky test runs, "port already in use" errors in subsequent tests, polluted coverage reports, and degraded CI agent performance.

**Business goal**: Ensure that when a test worker times out, all processes spawned by that worker (the entire process hierarchy) are completely and cleanly terminated, preventing orphaned background processes from holding system resources, polluting test environments, or causing flaky test failures in subsequent runs.

**Implementation language**: Python (part of the parallel test runner toolchain and test suite).

## User Stories

- As a **developer running `make test`**, I want any timed-out test worker and all of its spawned child processes to be cleanly terminated so that background processes don't keep running on my workstation, consuming battery/CPU or blocking ports needed for subsequent runs.
- As a **CI / pipeline operator**, I want worker timeouts to leave the runner agent completely clean without orphaned background processes, so that subsequent pipeline jobs or test suites on the same agent run in a predictable, unpolluted environment.
- As a **test author developing integration or server tests**, I want processes spawned by my tests (such as local servers or GUI offscreen runners) to be reliably cleaned up if my test hangs or times out, so that follow-up tests don't fail due to resource or port collisions.
- As a **maintainer reviewing test execution logs**, I want clear observability and logs indicating that a timed-out worker and its process tree were torn down, without cryptic crash errors or hung processes.

## Definition of Done

- When a worker exceeds its timeout limit, the test orchestrator terminates the entire hierarchy of processes associated with that worker, rather than just the direct worker process.
- No orphaned grandchild or child processes spawned by a timed-out worker remain running after the worker timeout handling completes.
- Shared system resources (e.g., local ports, open file descriptors, memory) allocated by the worker or its children are freed upon timeout teardown.
- Teardown of the worker process hierarchy handles already-terminated or partially-exited processes gracefully without raising unhandled errors or crashing the orchestrator.
- Existing timeout observability (status classification as timed out, structured timeout logging) is preserved and accurately reflects worker termination.
- Automated tests verify that when a worker process spawning child/grandchild processes times out, all descendant processes are terminated and no orphaned processes linger.
- All repository checks pass via standard `make` targets (`make lint`, `make test`).
- Documentation in developer guides (`doc/dev/parallel_test_runner.md`) is updated if operator-facing behaviors or guarantees are modified.

## Task Description

### Problem

In the parallel test runner, each worker executes a test file in an isolated process. When a worker hangs or deadlocks, the orchestrator detects the timeout and terminates the direct worker process. However, test fixtures and suites often launch additional child or background processes (e.g., external commands, offscreen display helpers, mock servers, sub-workers). If only the parent worker process is terminated, these descendant processes are reparented to init/systemd and become orphaned background processes.

These orphans continue to run detached, retaining bound ports, temporary files, and system resources. This causes intermittent and hard-to-diagnose failures in later tests that attempt to bind the same ports or access the same test directories, destabilizing the entire CI and local development workflow.

### Scope

**In scope**:
- Complete teardown of the worker process hierarchy upon timeout, ensuring all descendant processes are terminated.
- Graceful error handling during teardown if processes in the hierarchy terminate independently before or during cleanup.
- Automated tests demonstrating that worker children and grandchildren are terminated when a worker times out.
- Verification that non-timed-out workers (successful runs or normal failures) remain unaffected and clean up as expected.
- Documentation updates to developer documentation describing the hardened process teardown guarantees.

**Out of scope**:
- Changing the timeout duration defaults or configuration flags established in PYPOST-1192.
- Modifying individual test modules or test suite implementations to manually track their own subprocesses.
- Non-timeout process cleanup for tests outside the parallel runner orchestrator.
- Modifying unrelated parts of the parallel test runner (e.g., argument parsing refactors, test file ordering heuristics, or coverage combine subprocess timeouts).

### Constraints and Assumptions

- The solution must work reliably in the target operating environment (Linux/POSIX environments used in CI and development).
- The orchestrator must never hang or crash during teardown, even if child processes are unresponsive or already deceased.
- Process hierarchy cleanup must only target processes belonging to the specific timed-out worker; it must never terminate unrelated workers, the orchestrator itself, or other host system processes.
- Repository operations and test validation must be performed strictly using `make` targets.

## Functional Requirements

1. **Process Tree Isolation**: Each worker must be executed in a dedicated process context that allows identifying and controlling all child and descendant processes spawned within that worker's lifecycle.
2. **Hierarchy Termination on Timeout**: When a worker execution exceeds the configured wall-clock timeout, the orchestrator must terminate the direct worker process and all descendant processes spawned by that worker.
3. **Resilience to Premature Process Exit**: If a child or grandchild process terminates naturally before or during teardown, the orchestrator must handle missing process identifiers gracefully without failing or leaking unhandled exceptions.
4. **Complete Resource Reclaim**: Process termination must be final and unyielding so that stubborn or hanging child processes cannot resist termination and remain alive indefinitely.
5. **Preservation of Outcome and Diagnostics**: The timeout outcome (`TIMED_OUT`), error classification, and structured logging for the affected test file must be retained and reported accurately to the orchestrator summary.

## Non-Functional Requirements

- **Reliability & Determinism**: Test runs must leave zero leftover processes after timeouts occur, ensuring reproducible test execution across repeated runs.
- **Safety & Process Confinement**: Teardown must be strictly confined to the specific worker's process tree to avoid killing sibling workers, the parent orchestrator, or unrelated host system processes.
- **Speed**: Timeout teardown should complete promptly without introducing unnecessary delays into the test suite run.
- **Robustness**: The teardown logic must not fail or raise uncaught errors under race conditions (e.g., process terminating while teardown signal is sent).

## Main Entities

- **Test Orchestrator**: Manages parallel worker lifecycles, monitors execution durations against the configured timeout, and initiates teardown when a timeout occurs.
- **Test Worker**: An execution process launched by the orchestrator to run a pytest suite or test file.
- **Worker Process Tree**: The hierarchy comprising the root test worker and any child, grandchild, or helper processes spawned during test execution.
- **Timeout Boundary**: The maximum allowable wall-clock duration for a worker before it is declared timed out.
- **Teardown Controller**: The mechanism responsible for signaling and ensuring the termination of the entire worker process tree upon timeout.

## User Scenarios

1. **Worker with spawned child processes times out**:
   A test worker launches background subprocesses (e.g., a background server or helper tool). The test hangs and exceeds the worker timeout. The orchestrator triggers teardown, terminating the worker and all its child/grandchild processes. Once teardown completes, no processes from that worker remain running, and ports/resources are immediately available for subsequent workers.

2. **Normal worker execution (no timeout)**:
   A test worker runs and completes within the timeout limit. The worker exits normally. The orchestrator records the test outcome without triggering forced timeout teardown.

3. **Child process exits just before timeout**:
   A worker's child process exits just as the timeout triggers. The teardown logic encounters an already-exited process and handles it cleanly without raising errors or crashing the orchestrator run.

4. **Stubborn child process**:
   A worker spawns a child process that ignores standard termination signals. The teardown logic ensures that stubborn child processes are forcefully terminated so they cannot linger as zombies or detached daemons.

## Q&A

**Why is process tree termination necessary if Python already handles timeouts?**
By default, standard subprocess timeout handling terminates only the immediate child process. Any processes spawned by that child become detached orphans and continue running in the background, which consumes CPU/memory and locks shared resources like ports and files.

**Does this change the default timeout or configuration flags?**
No. The default timeout (30s / 120s in Makefile) and the `--worker-timeout` / `WORKER_TIMEOUT` configuration introduced in PYPOST-1192 remain unchanged. This task hardens the teardown behavior when that timeout expires.

**Could killing the process tree accidentally kill other test workers?**
No. A key requirement is strict isolation: each worker's process hierarchy must be isolated such that terminating a timed-out worker's process tree affects only that worker and its descendants, never sibling workers or the orchestrator.

**What happens if a process in the tree has already exited when teardown occurs?**
The teardown process must be idempotent and resilient to race conditions, safely ignoring processes that have already exited.
