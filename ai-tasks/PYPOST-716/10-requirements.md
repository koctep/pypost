# PYPOST-716: Stabilize MCPServerManager port-busy test

**Programming Language:** Python

## Goals

From a business and developer productivity perspective, a highly reliable, robust, and stable
test suite is critical for continuous integration and continuous delivery (CI/CD). Native crashes
or segfaults (SIGSEGV) in the test suite on macOS cause significant developer friction:
- They abruptly halt `make test` or `make test-cov`, causing developer frustration and blocking
  local work.
- They delay pull request feedback and introduce noise/flakiness in local test environments.
- They undermine trust in the automated test suite, which is a key pillar of PyPost's regression
  safety.

The goal of this task is to stabilize the port-busy test scenario for the MCP Server Manager and
Metrics Server on macOS, ensuring that tests fail or succeed gracefully without native PySide6 or
asyncio thread-termination crashes. This keeps the test suite stable and green for macOS and
other developer environments.

## User Stories

- **As a developer running the PyPost test suite on macOS**, I want the port-busy test cases to run
  cleanly and report failures or success gracefully without causing a native segfault (SIGSEGV),
  so that the entire local test suite can complete and provide helpful feedback.
- **As a CI operator / Release manager**, I want the test suite to execute reliably across all
  supported platforms so that automated pipelines can run to completion without intermittent,
  environment-specific crashes.
- **As an operator or user**, I want to receive clear, accurate bind-failed error messages if the
  port is busy, rather than having the application crash natively.

## Definition of Done

This section describes when the task is considered `done`, with a list of acceptance criteria
(business logic verification).

- [ ] All tests in `tests/test_mcp_server_manager.py` run cleanly to completion on macOS without
  native segfaults.
- [ ] All tests in `tests/test_metrics_server_startup.py` run cleanly to completion on macOS
  without native segfaults.
- [ ] The `make test` and `make test-cov` suites run successfully and report accurate results.
- [ ] Bind failure error handling is still functional and verified (the application emits start
  failed signals when a port is busy under normal circumstances).
- [ ] No regression is introduced in test coverage.

## Task Description

**Problem:**
The test cases `test_port_busy_emits_start_failed` in `tests/test_mcp_server_manager.py` and
`tests/test_metrics_server_startup.py` allocate a free port, occupy it using a helper socket
`_occupy_port()`, and then attempt to start the server (either `MCPServerManager` or
`MetricsManager`) on that occupied port.
Inside a daemon/background thread, `_run_uvicorn()` is started. When `uvicorn` fails to bind, it
gets intercepted and should raise a clean Python exception or fail gracefully.
However, under macOS with PySide6, raising this exception or having uvicorn attempt to clean up /
exit inside a background thread triggers a native C++ segfault (SIGSEGV) which aborts the entire
pytest process, rather than raising a clean Python exception or exiting gracefully.

**Business intent:**
Ensure developer productivity and local test suite reliability on macOS is not disrupted by
native crashes under expected failure scenarios.

### In Scope
- `tests/test_mcp_server_manager.py`
- `tests/test_metrics_server_startup.py`
- Stabilization of the specific port-busy test cases (`test_port_busy_emits_start_failed`).
- Ensuring that the rest of the test suite and production bind error signaling are not compromised.

### Out of Scope
- Rewriting the entire threading/asyncio architecture of `MCPServerManager` or `MetricsManager`
  (unless required for stabilization, while focusing on ensuring tests run stably without causing
  native crashes).
- Resolving the general native Qt/PySide6 thread cleanup crash tracked under PYPOST-429.

### Functional Requirements
- The system must correctly detect when a port is busy/occupied.
- The system must emit a clear, operator-facing bind/startup error message.
- The system must transition to the stopped status when a start fails.
- The test suite must be able to assert that this failure detection and notification mechanism
  works, without aborting/segfaulting the test runner process.

### Non-Functional Requirements
- **Stability:** The test execution must be completely stable on macOS (zero segfaults).
- **Graceful degradation:** If a native crash is unavoidable due to macOS environment
  limitations, the test suite must handle this gracefully and complete stably.

### Constraints and Assumptions
- The native segfault is caused by PySide6 / uvicorn / thread interaction on macOS, currently
  tracked by the team in PYPOST-429.
- The test suite must complete stably without crashing the process under macOS, and the server
  managers must gracefully handle busy ports under normal operation.

### Main Entities (Business View)

| Entity | Description |
| --- | --- |
| MCPServerManager | Manager class for starting, stopping, and tracking status of the MCP Server. |
| MetricsManager | Manager class for starting, stopping, and tracking Metrics Server status. |
| Port Busy Test Case | Test verifying that starting a server on an already bound/occupied port. |
| Start Failed Signal | Qt Signal emitted with the bind failure message when server cannot start. |
| Port-Busy Scenario | A situation where a local port is already bound by another process. |
| Startup Error Event | Event indicating server failed to start due to port unavailability. |
| Exception Handler | Component or logic that catches and processes startup exceptions. |

## Q&A

### Why does this only fail on macOS?
Under macOS, `sys.exit` interception combined with uvicorn's thread cleanup inside PySide6
causes native thread destruction/resource release issues (tracked in PYPOST-429).

### What is expected during a port-busy scenario?
The server managers must handle busy ports gracefully, and the test suite must complete stably.

### Does this affect Linux/Windows?
No, the segfault has only been observed on macOS Python 3.11+.

### Is production code affected?
The application does not typically experience this crash in production because uvicorn is not
continuously started/stopped/interrupted inside PySide6 tests on busy ports. However, a robust
test suite is needed for dev-gating.
