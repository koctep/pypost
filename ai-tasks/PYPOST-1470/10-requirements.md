# PYPOST-1470: Process-mode 10x stress parity + Windows stop CI

## Goals

PyPost supports both thread-based and process-based isolation for Model Context Protocol (MCP)
servers. While thread mode has proven high-density stress test coverage (10+ concurrent servers),
process-mode execution requires full operational parity under equivalent high-load conditions.
In enterprise deployments, process isolation is preferred for fault containment, memory hygiene,
and tenant separation.

The business goals for this task are:
- Multi-Tenant Density and Scale: Ensure 10+ concurrent MCP server processes can start up, run,
  and shut down reliably on a single host without resource exhaustion or deadlocks.
- Production Resilience and Fault Recovery: Guarantee that process workers survive abrupt client
  disconnections (TCP RST mid-payload) and cleanly recover without crashing or corrupting state.
- Resource Hygiene and Port Reclamation: Prevent operating system resource leaks by ensuring
  all process handles, file descriptors, and network ports are immediately released on shutdown.
- Enterprise Cross-Platform Stability: Windows environments manage process lifecycles via Win32
  `TerminateProcess` semantics rather than POSIX signals (`SIGTERM`/`SIGKILL`). Automated CI must
  validate that process supervisor stop escalation functions deterministically on Windows runners
  without leaving hung processes or zombie tasks.

## User Stories

### Operator
As a platform operator running multi-tenant PyPost instances,
I want 10+ concurrent process-isolated MCP servers to reliably start, serve, and terminate cleanly,
So that multi-tenant workloads remain stable without port conflicts, socket leaks, or host OOM.

### Developer
As an API and tool integration developer,
I want isolated MCP worker processes to maintain strict variable and environment namespace privacy
under heavy concurrent load,
So that simultaneous requests to distinct servers never experience cross-talk or state pollution.

### CI / Release Maintainer
As a continuous integration and release maintainer,
I want automated stress tests and Windows process termination escalation suites running in CI,
So that regressions in process lifecycle management, signal handling, or port rebinding are caught
before release without hanging CI build runners.

## Definition of Done

This task is complete when the following acceptance criteria are fulfilled:
1. 10x Process Barrier Startup:
   - Exactly 10 standalone MCP servers configured in process execution mode are launched
     simultaneously using barrier synchronization.
   - All 10 worker processes successfully transition to the running state and report active
     listening status.
   - Concurrent tool discovery requests across all 10 running processes succeed without timeouts
     or deadlocks.
2. 10x Concurrent Namespace Isolation:
   - 10 standalone process-mode servers configured with distinct values for identical variable keys
     process concurrent request traffic.
   - All responses demonstrate strict data isolation with zero cross-talk or state leakage across
     worker processes.
3. 10x Abrupt Client Disconnect Resilience:
   - Abrupt socket termination (TCP RST mid-request) is simulated across 10 concurrent process-mode
     servers.
   - All 10 worker processes remain alive, healthy, and able to process subsequent valid client
     tool calls.
4. 10x Concurrent Teardown and Port Reclamation:
   - Parallel shutdown of all 10 server processes terminates all child processes cleanly within the
     allocated stop budget.
   - All 10 allocated network ports are immediately re-bindable by standard TCP listening sockets
     with zero `EADDRINUSE` port collision errors.
5. Cross-Platform Windows Stop Escalation Verification:
   - Process termination escalation (graceful stop request escalating to forceful termination) is
     verified under Windows process lifecycle semantics.
   - CI automation includes Windows runner coverage exercising process stop escalation to verify
     no orphan worker processes, zombie handles, or hanging runners occur.
6. Documentation & Quality Standards:
   - Task metadata documents implementation language as Python.
   - All tests run within bounded execution timeouts and pass through project `make` targets.

## Task Description

### Business Problem
PyPost provides process-isolated MCP servers to ensure that a crash or memory leak in one server
does not compromise other running servers or the host application. While thread-mode servers
feature extensive 10x stress testing, process-mode servers lack parity coverage under identical
high-density conditions.

Furthermore, Windows environments do not implement POSIX signal semantics (`SIGTERM`, `SIGKILL`),
relying instead on Win32 termination primitives. Without automated validation on Windows runners,
uncooperative or frozen child worker processes risk leaking system resources or causing test
runners to hang indefinitely during continuous integration.

### Goals and Scope
- Establish 10x multiserver stress test parity for process mode (`mcp_execution_mode = "process"`):
  - Barrier-synchronized concurrent startup.
  - High-concurrency variable namespace isolation.
  - Abrupt TCP RST client disconnection fault tolerance.
  - Parallel teardown with immediate port reclamation and process cleanup.
- Implement automated CI verification on Windows for process supervisor stop escalation:
  - Verify cooperative stop escalation to forceful termination under Win32 semantics.
  - Ensure zero orphaned processes remain on host systems following worker shutdown.

### Scope Boundaries
- In Scope:
  - Process-mode high-density (10x) stress testing scenarios matching thread-mode benchmarks.
  - Windows CI workflow integration for process stop escalation.
  - Automated verification of child process lifecycle and socket reclamation under stress.
- Out of Scope:
  - Modifications to the core MCP protocol specification or message schema.
  - User interface components for settings configuration (tracked under separate tickets).
  - Operating system kernel tuning or container orchestration layers.

### Constraints and Assumptions
- Implementation Language: Python.
- Tooling Standard: All verification and testing operations must run through Makefile targets.
- Bounded Execution: All stress tests and termination sequences must define strict timeouts to
  prevent CI pipeline deadlocks.
- Backward Compatibility: Existing thread-mode multiserver stress tests and behaviors must remain
  fully functional and intact.

### Non-Functional Requirements
- Reliability: 100% of child processes must be cleaned up on server stop, leaving zero orphaned or
  zombie processes.
- Concurrency: Zero race conditions or deadlocks during concurrent multi-process initialization
  and teardown.
- Portability: Process supervision and stop escalation must operate reliably across Linux, macOS,
  and Windows platforms.

## Q&A

### Q1: Why is 10x density specifically required for process mode?
A1: Thread mode already proves stability across 10 concurrent servers. Enterprise deployments
frequently host 10 or more isolated tools simultaneously. Parity testing at 10x ensures the
process supervisor handles operating system process table pressure, IPC pipe allocation, and port
reclamation at scale.

### Q2: How does stop escalation differ on Windows compared to POSIX systems?
A2: POSIX platforms send `SIGTERM` followed by `SIGKILL` if the process does not terminate within
the timeout. Windows uses `TerminateProcess` via Win32 process handles. The supervisor must manage
these differences transparently so that uncooperative workers are terminated reliably on both
platforms.

### Q3: Why is Windows CI coverage necessary if unit tests run on Linux?
A3: Process management behavior, handle cleanup, and socket reuse semantics vary significantly
between Linux and Windows. Running dedicated Windows CI checks ensures platform-specific process
leaks or deadlocks are discovered before release.
