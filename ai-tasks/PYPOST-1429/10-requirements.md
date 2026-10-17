# PYPOST-1429: Encapsulate Subprocess Stdio IPC Harness

## Goals

In Model Context Protocol (MCP) server development, standard input/output (stdio) represents a core transport mechanism alongside HTTP/SSE network streams. Testing MCP stdio transports requires spawning child processes that run server instances, exchanging framed JSON-RPC messages across bi-directional operating system pipes (stdin and stdout/stderr), managing asynchronous stream draining, and handling clean process lifecycles.

During the development of live wire IPC repro testing in `tests/test_mcp_standalone_wire_ipc_repro.py`, stdio child process management was implemented directly within a test function (`test_stdio_subprocess_ipc_large_payload_and_burst`). While this verified the immediate capability of handling burst traffic and large payloads, it embedded low-level process and pipe mechanics directly inside test scenario code, creating significant technical debt:

1. **Deadlock and Resource Leak Risks**: Manual management of raw OS pipes, background reader threads, and child process lifecycles carries substantial risk. If a child process produces voluminous output (>64KB OS pipe buffer capacity) while stdout/stderr are not continuously and asynchronously drained, OS pipe buffers saturate and cause indefinite deadlocks. Furthermore, test assertion failures or unexpected exceptions can bypass cleanup steps, leaving orphaned child processes, leaked file descriptors, and hung worker threads in CI runners.
2. **Lack of Reusability**: Other existing and upcoming MCP test suites (such as MCP client-server integration suites, CLI command execution suites, and protocol error handling tests) require identical stdio child process execution, asynchronous message consumption, and timeout-enforced response handling. Forcing every test suite to reimplement subprocess management leads to widespread code duplication.
3. **High Cognitive Load and Fragile Test Logic**: Mixing low-level process creation, stream decoding, thread synchronization, and timeout loops with high-level test assertions makes tests difficult to read, reason about, and maintain.

The primary business goal of this task is to eliminate technical debt by encapsulating child process management, asynchronous stream reading, and timeout enforcement into a dedicated, reusable test helper module in `tests/helpers/mcp_stdio_harness.py`. This ensures safe, leak-free, deadlock-free process execution across the testing ecosystem and accelerates the development of reliable MCP stdio transport tests.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **MCP Test Automation Engineer**, I want a reusable stdio subprocess harness helper in `tests/helpers/` so that I can construct stdio transport tests without manually managing subprocess lifecycles, background worker threads, and OS pipe buffers.
- As an **MCP Feature Developer**, I want expressive abstractions for starting child processes, sending messages, waiting for correlated responses with enforced timeouts, and cleanly terminating processes so that my test suites stay focused on protocol assertions rather than plumbing.
- As a **CI / Quality Engineer**, I want guaranteed termination and cleanup of child processes and reader threads even in the event of assertion failures, timeouts, or unhandled errors so that CI build agents never experience hung jobs or resource exhaustion from zombie processes.
- As a **Core Maintainer**, I want `tests/test_mcp_standalone_wire_ipc_repro.py` refactored to consume the shared harness helper so that test complexity is reduced, code duplication is eliminated, and existing wire stress test assertions pass with zero regressions.

## Definition of Done

This task is considered complete when:
1. Reusable subprocess stdio IPC harness capabilities are encapsulated in a dedicated test helper module at `tests/helpers/mcp_stdio_harness.py`.
2. The helper provides clean abstractions for child process lifecycle control (starting, graceful shutdown, forceful termination, and context manager support), message dispatch over stdin, non-blocking asynchronous draining of stdout and stderr, and timeout-enforced response retrieval.
3. The existing test `test_stdio_subprocess_ipc_large_payload_and_burst` in `tests/test_mcp_standalone_wire_ipc_repro.py` is refactored to consume the new helper, eliminating inline thread and process management while preserving all existing test assertions (including burst traffic and large payload >64KB handling).
4. The helper guarantees robust cleanup to prevent zombie processes, leaked pipe handles, and unjoined threads under both successful and failing test runs.
5. All test suites in `tests/test_mcp_standalone_wire_ipc_repro.py` pass without behavioral changes or regressions.
6. Repository quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass with zero errors.

## Task Description

### Problem Statement

The `test_stdio_subprocess_ipc_large_payload_and_burst` test currently manages raw child process handles, two dedicated daemon threads for stdout and stderr, thread synchronization locks, and custom timeout polling loops directly in the test body. This approach violates separation of concerns, introduces risks of test flakiness or hangs if deadlines are breached or exceptions occur, and cannot be reused by other test suites requiring stdio subprocess execution.

### Scope

- **Create Dedicated Shared Helper**:
  - Implement a reusable subprocess stdio IPC harness in `tests/helpers/mcp_stdio_harness.py`.
  - Provide safe lifecycle management (start, stop, context manager integration).
  - Implement asynchronous, non-blocking draining of standard output and standard error streams.
  - Implement message sending and correlated response waiting with configurable deadlines and timeout enforcement.
  - Implement guaranteed teardown semantics (clean stdin close, bounded wait, and fallback process termination).
- **Refactor Existing Test Suite**:
  - Update `tests/test_mcp_standalone_wire_ipc_repro.py` to import and utilize `tests/helpers/mcp_stdio_harness.py`.
  - Remove redundant inline subprocess and thread handling from the test file.
  - Maintain all functional assertions: handshake initialization, notification sending, 50-request burst processing, large payload (>64KB) verification without pipe stalling, and clean shutdown on stdin closure.
- **Verification and Quality Compliance**:
  - Ensure full static type hints and docstring documentation.
  - Validate against repository quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`).

### Out of Scope

- Modifying runtime production code in `pypost/` (this task is strictly test helper encapsulation).
- Modifying MCP stdio transport implementation in the core application or server runtime.
- Altering the scenario contracts or payload expectations in `test_stdio_subprocess_ipc_large_payload_and_burst`.
- Implementing test harnesses for other transport types (TCP wire client is already covered in PYPOST-1428).

### Functional Requirements

- **FR1 (Subprocess Lifecycle Management)**:
  - Provide capabilities to launch a Python or external child process with piped standard streams (`stdin`, `stdout`, `stderr`).
  - Support Python context management (`with` statement) to guarantee initialization and deterministic cleanup.
  - Support graceful termination by closing `stdin` and waiting for clean process exit within a configurable timeout, with automatic forceful process termination if the process does not terminate within the deadline.
- **FR2 (Asynchronous Stream Draining & Deadlock Prevention)**:
  - Continuously and asynchronously drain both `stdout` and `stderr` streams to prevent OS pipe buffers from filling and deadlocking the child process.
  - Correctly handle large payloads exceeding standard OS buffer sizes (such as 70KB+ message bursts) without truncation, corruption, or blocking.
- **FR3 (Message Transmission & Response Retrieval)**:
  - Provide methods to transmit structured messages (JSON-RPC) or raw lines to the child process's standard input and flush immediately.
  - Provide capabilities to await responses by message identifier or predicate with strict timeout enforcement.
  - Safely synchronize collected responses across concurrent draining workers.
- **FR4 (Diagnostic Capture)**:
  - Collect and preserve standard error output and stream decoding errors for post-mortem diagnostics when a child process exits abnormally or times out.
- **FR5 (Seamless Test Suite Integration)**:
  - Provide a clean, modular import interface under `tests/helpers/`.
  - Refactor `tests/test_mcp_standalone_wire_ipc_repro.py` to use the helper, preserving all existing stress test assertions and achieving identical or superior test execution stability.

### Non-Functional Requirements

- **NFR1 (Zero Flakiness and Deterministic Timeouts)**: All wait, read, and termination operations must enforce bounded timeouts to guarantee tests never hang indefinitely in automated CI pipelines.
- **NFR2 (Resource Safety)**: Zero leaked operating system processes, zero lingering threads, and zero unclosed file descriptors, regardless of whether tests complete successfully or raise assertion errors.
- **NFR3 (Maintainability and Standards Compliance)**: Full adherence to repository Python standards, including PEP 8 formatting, flake8 linting, mypy type verification, and comprehensive docstring documentation.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Stdio IPC Harness** | Shared test utility module providing encapsulated subprocess management for stdio transport testing. | Module path (`tests/helpers/mcp_stdio_harness.py`), exposed classes, lifecycle methods. |
| **Subprocess Test Session** | An active child process instance running under test control. | Process identifier (PID), execution status, pipe streams, timeout configuration. |
| **Asynchronous Stream Drainer** | Background draining mechanism reading child stdout and stderr without blocking the test runner. | Target stream (stdout/stderr), captured lines/messages, captured error log. |
| **Response Registry** | Thread-safe collection of received and parsed messages from the child process. | Message collection, lookup keys (message id), arrival notifications. |
| **Consumer Test Suite** | Test module validating MCP server stdio behavior. | Test file (`tests/test_mcp_standalone_wire_ipc_repro.py`), scenario assertions. |

### User Scenarios

#### Scenario 1: Executing Existing Subprocess Stdio Stress Test
During automated test runs, `tests/test_mcp_standalone_wire_ipc_repro.py` runs `test_stdio_subprocess_ipc_large_payload_and_burst`. The test uses the encapsulated stdio harness to spawn the standalone MCP server child process, send an initialization handshake, transmit a 50-request burst (including 70KB payloads), wait for all responses, and close stdin. The harness safely drains streams in the background, enforces timeouts on response collection, and terminates the child process cleanly upon exit.

#### Scenario 2: Developing a New Stdio-Based MCP Test
A developer implements a new test verifying MCP protocol error handling or CLI invocation over stdio. Instead of writing custom subprocess execution and pipe reading logic, the developer imports `mcp_stdio_harness` from `tests.helpers`, instantiates the harness via a context manager, and executes test scenarios with reliable timeout guarantees and automatic cleanup.

## Q&A

**Q: Why is encapsulating child process management into a helper necessary?**  
A: Spawning child processes with raw OS pipes without a structured harness is notoriously prone to deadlocks (when buffers exceed OS limits) and process leaks (when exceptions occur before cleanup). Encapsulating this logic provides safe, tested, and reusable infrastructure for all stdio-based tests in the repository.

**Q: Why must stream reading be asynchronous and non-blocking?**  
A: OS pipe buffers have finite capacity (typically 64KB on Linux). If a child process writes more data to stdout or stderr than the pipe buffer can hold while the parent process is blocked waiting to write or not actively reading, both processes deadlock. Asynchronous draining ensures pipe buffers are continuously emptied.

**Q: Does this task involve modifying production runtime code?**  
A: No. This task is purely focused on test infrastructure and test technical debt reduction. Production application code in `pypost/` remains untouched.
