# PYPOST-1434: Concurrent Server Teardown and Parallel Cleanup Support

## Goals

In integration test suites and multi-server orchestration workflows, PyPost spins up multiple standalone Model Context Protocol (MCP) servers (frequently 5 or more servers concurrently) to emulate heterogeneous tool providers, collection catalogs, and environment variables. During test fixture cleanup and application shutdown, all registered servers must be stopped cleanly to release local network sockets, free background execution resources, and prevent cross-test contamination.

Under the current sequential shutdown mechanism in `MCPServerRegistry.stop_all()` and `ServerRegistryFixtureMixin.teardown()`, teardown iterates through each server instance one after another on the calling thread. If each server requires a graceful drain interval or wait period (e.g. 1 to 2 seconds to signal termination, close active HTTP/SSE connections, and finish background routines), sequential teardown incurs additive latency ($N \times \text{drain time}$). When running multi-server test matrices or large CI suites with dozens of integration tests, this cumulative delay adds significant minutes to total test execution time and delays developer feedback loops. Furthermore, if a single server encounters an unhandled exception or blocks during its shutdown sequence, sequential iteration risks stalling or aborting the teardown of subsequent servers, leaving orphaned background threads and bound TCP ports that cause cascading failures in downstream tests.

The primary goal of this task is to upgrade `MCPServerRegistry.stop_all()` and `ServerRegistryFixtureMixin.teardown()` to terminate registered servers concurrently using a bounded thread pool and bounded join timeout. This concurrent cleanup architecture must:
1. **Accelerate Teardown Performance**: Drastically reduce multi-server teardown duration from cumulative sequential latency ($O(N)$) to the maximum single server teardown duration plus minor coordination overhead ($\max(T_i) + \epsilon$).
2. **Handle Partial Failures Resiliently**: Ensure that a failure, slow response, or exception in one server's shutdown routine does not block, delay, or prevent the teardown of remaining registered servers.
3. **Guarantee Deterministic Cleanup & Resource Hygiene**: Ensure all servers are stopped and their underlying resources (network ports, background threads) are released before the teardown method returns, preventing resource leaks, port collisions, or flaky test execution.
4. **Preserve 100% Backward Compatibility**: Maintain the existing synchronous invocation contract and method signatures of `MCPServerRegistry.stop_all()` and harness `teardown()` / `close()`, ensuring zero breaking changes for existing test suites, fixtures, or application runtime callers.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **integration test author**, I want test suites running multiple MCP servers to terminate all servers concurrently during fixture teardown, so that my local test runs complete quickly without unnecessary cumulative delays.
- As a **CI / DevOps engineer**, I want test harness cleanup across multi-server suites to execute in parallel, so that CI pipeline runtimes are reduced, runner capacity is freed up, and PR verification feedback is delivered faster.
- As a **developer running test matrices with failing or misbehaving servers**, I want server teardown to be resilient against individual failure modes, so that an exception or slow drain in one server does not leave other servers running in the background and polluting subsequent test environments.
- As a **core platform maintainer**, I want `MCPServerRegistry.stop_all()` and test harness `teardown()` to retain identical public method signatures and synchronous completion semantics, so that existing callers, pytest fixtures (`collection_integration_harness`, `collection_harness`), and production shutdown sequences continue to work without modification.
- As a **system administrator / runtime operator**, I want orderly, bounded, and parallel shutdown of all registered servers upon application termination, so that operating system ports and network sockets are promptly recycled without entering stale or orphaned states.

## Definition of Done

This task is considered complete when:
1. **Concurrent Server Termination**: `MCPServerRegistry.stop_all()` and `ServerRegistryFixtureMixin.teardown()` initiate and execute server termination concurrently across all registered active/candidate server instances rather than sequentially.
2. **Bounded Execution & Join Timeout**: Parallel teardown execution is governed by a bounded worker pool and a deterministic join timeout, ensuring that teardown does not block indefinitely if a server hangs.
3. **Resilient Error Isolation & Aggregation**: If one or more servers raise an error or experience unexpected behavior during teardown, the system isolates each failure, completes teardown attempts for all remaining servers, aggregates and logs all encountered issues, and avoids unhandled cascading crashes.
4. **Deterministic Resource Hygiene**: Upon completion of `stop_all()` or `teardown()`, all server managers are transitioned to stopped state, background threads are terminated, and assigned dynamic ports are freed for immediate reuse.
5. **Idempotence & Thread Safety**: Repeated or concurrent calls to `stop_all()`, `teardown()`, or `close()` are safe, idempotent no-ops that do not raise errors or trigger double-close race conditions.
6. **100% Backward Compatibility**: Public signatures (`stop_all() -> None`, `teardown() -> None`, `close() -> None`) and synchronous completion behavior are fully preserved. Callers are guaranteed that all shutdown work has finished before the call returns.
7. **Comprehensive Test Verification**:
   - Automated tests demonstrate concurrent termination across multiple servers (e.g. 5+ servers) with measurable execution time scaling with $\max(\text{teardown time})$ rather than the sum of teardown times.
   - Tests verify resilient error handling when an individual server fails during parallel teardown.
   - Tests assert idempotent multiple teardowns and immediate port reusability.
8. **Quality Gate Compliance**:
   - All tests pass under `make test` and `make check`.
   - Static analysis passes under `make lint` and `make typecheck` without warnings or regressions.
   - AI task artifacts pass verification under `make verify-ai-tasks`.

## Task Description

### Problem Statement

PyPost provides comprehensive multi-server integration capabilities, allowing test suites to spin up multiple standalone MCP servers to validate variable resolution, catalog manifests, and tool invocation. In scenarios with multiple servers (such as 3 to 10 instances), cleaning up those servers at the end of each test represents a significant portion of test execution time.

Currently, `MCPServerRegistry.stop_all()` sequentially iterates through registered server managers, invoking `stop()` on each instance one at a time. Likewise, `ServerRegistryFixtureMixin.teardown()` delegates to `self.registry.stop_all()`. If each server requires time to drain connections, complete in-flight requests, and signal worker threads, total teardown duration is strictly additive:
$$\text{Teardown Duration} = \sum_{i=1}^{N} T_{\text{drain}}(i)$$

For 5 servers with a 1.0s drain time, teardown takes 5.0 seconds per test. In a test file with 10 test functions, server teardown alone accounts for nearly a minute of dead wait time. Furthermore, sequential iteration is vulnerable to single-point stalls: if server 1 encounters an exception or hangs on thread join, servers 2 through 5 are either delayed or never stopped at all.

By upgrading `MCPServerRegistry.stop_all()` and `ServerRegistryFixtureMixin.teardown()` to concurrent execution, termination signals and join waits are executed in parallel across a bounded worker pool. Aggregate teardown latency drops to:
$$\text{Teardown Duration} \approx \max_{i=1}^{N} \left( T_{\text{drain}}(i) \right) + \epsilon$$

This reduces teardown overhead by up to 80% or more for multi-server tests while ensuring all servers receive shutdown signals even if one server encounters issues.

### Scope

- **In Scope**:
  - Upgrading `MCPServerRegistry.stop_all()` to terminate all registered server instances concurrently using a bounded thread pool and bounded join timeout.
  - Ensuring `ServerRegistryFixtureMixin.teardown()` and `close()` in `tests/helpers/collection_integration_harness.py` benefit from concurrent shutdown while preserving safe exception isolation.
  - Providing resilient error aggregation and structured logging when errors occur during parallel termination.
  - Ensuring deterministic status updates (transitioning instances to stopped state) and resource release.
  - Maintaining full backward compatibility for all existing callers across unit tests, integration tests, UI controllers, and daemon runtime.
  - Adding unit and integration tests verifying concurrent termination, timing speedup, error isolation, and idempotence.
- **Out of Scope**:
  - Changing single-server shutdown logic in `MCPServerRegistry.stop(instance_id)` or `MCPServerManager.stop_server()`.
  - Modifying server startup, readiness polling, or candidate validation logic.
  - Changing client-side communication protocols or JSON-RPC handlers.
  - Altering production UI workflows or adding user-facing UI controls.

### Functional Requirements

- **FR1: Concurrent Multi-Server Shutdown**:
  - `MCPServerRegistry.stop_all()` must trigger termination for all registered server instances in parallel rather than sequentially.
  - Pending reconfigurations and candidate managers must also be stopped concurrently and cleaned up safely.
- **FR2: Bounded Concurrency & Join Timeout**:
  - Parallel teardown must execute using a bounded worker pool to avoid unbounded thread creation.
  - The teardown coordinator must enforce a bounded wait timeout when awaiting completion of worker tasks, preventing teardown from hanging if a background process or thread becomes unresponsive.
- **FR3: Resilient Error Handling & Isolation**:
  - Teardown of any individual server must not be aborted or skipped because another server raised an exception or failed during its shutdown.
  - All exceptions encountered across worker tasks must be captured, logged with full diagnostic context (including server ID and error details), and handled safely without leaving dangling instances.
- **FR4: Deterministic State & Resource Release**:
  - All server instances must be recorded as stopped in the registry status tracking upon completion of their respective shutdown tasks.
  - OS network ports associated with stopped servers must be promptly released so that subsequent tests or operations can rebind without port collision errors.
- **FR5: Synchronous Caller Contract & Idempotence**:
  - `stop_all()` and harness `teardown()` must remain synchronous from the caller's perspective, blocking until all parallel tasks have completed or timed out.
  - Successive calls to `stop_all()`, `teardown()`, or `close()` on the same registry or harness must be safe, idempotent no-ops.
- **FR6: Full Backward Compatibility**:
  - The method signature of `stop_all()` must remain backward compatible, requiring no mandatory new parameters from existing callers.
  - All existing test fixtures and production call sites (such as `DaemonRuntime`, `McpServerController`, and pytest integration harnesses) must function without modification.

### Non-Functional Requirements

- **NFR1: Performance & Latency Scaling**:
  - Aggregate teardown duration for $N$ servers must scale with $\max(T_i) + \text{pool overhead}$, achieving substantial latency reduction compared to sequential execution for $N \ge 2$.
  - Overhead from thread pool management must be minimal (< 50ms under normal conditions).
- **NFR2: Reliability & Thread Safety**:
  - Concurrent teardown operations must be thread-safe and free of race conditions, deadlocks, or state corruption when accessing registry collections or status registries.
- **NFR3: Clean Resource Hygiene**:
  - Teardown must cleanly shut down worker pools, join background threads within bounded deadlines, and guarantee zero leaked threads or hanging handles.
- **NFR4: Observability & Diagnostics**:
  - Parallel teardown start, per-server termination progress, warnings/errors, and aggregate completion must be clearly logged at appropriate log levels (DEBUG/INFO/WARNING/ERROR) with instance identifiers and timing metrics.
- **NFR5: Code Quality & Repository Standards**:
  - Code must adhere to PEP 8 standards, maintain 100% type annotations compatible with mypy, include explicit test timeouts per repository testing rules, and use exclusively `make` targets for verification.

### System Entities & Domain Perspective

- **MCP Server Registry (`MCPServerRegistry`)**: Central management entity tracking all configured and active standalone MCP server instances, coordinating their lifecycles and global shutdown.
- **Server Registry Fixture (`ServerRegistryFixtureMixin` / Test Harness)**: Modular test fixture component responsible for provisioning, isolating, and tearing down MCP servers during automated testing.
- **Standalone Server Instance / Manager (`MCPServerManager`)**: Individual running server instance encapsulating background worker threads, network port bindings, and protocol endpoints.
- **Parallel Teardown Coordinator**: Concurrency mechanism responsible for dispatching stop operations across multiple server instances simultaneously, collecting execution results, and enforcing bounded join deadlines.
- **Teardown Result / Error Collector**: Structured aggregation of per-instance shutdown outcomes, recording successful terminations, timeouts, and encountered exceptions.

### User Scenarios & Use Cases

- **Scenario 1: Standard Multi-Server Integration Test Teardown**:
  A test fixture provisions 5 standalone MCP servers to validate distributed tool routing. At the end of the test, the harness invokes `teardown()`, which calls `registry.stop_all()`. All 5 servers are signaled and shut down in parallel. Total teardown takes approximately the time required for one server to drain (~1s) rather than 5 seconds. All TCP ports are immediately freed.
- **Scenario 2: Teardown with a Hanging or Slow Server**:
  A test induces high load or network stall on one server while other servers remain healthy. During test teardown, `stop_all()` concurrently signals all servers. Healthy servers terminate immediately. The slow server is joined with a bounded timeout. The coordinator logs a diagnostic warning for the slow server, marks all servers as handled, and returns without blocking the entire test runner.
- **Scenario 3: Teardown with Partial Server Exception**:
  One server throws an unexpected exception during its stop routine (e.g. socket already reset or filesystem handle closed). The parallel teardown coordinator traps the exception, continues terminating the other 4 servers to completion, and logs the captured error. The test environment is cleanly restored without cascading failures.
- **Scenario 4: Idempotent or Repeated Teardown Invocations**:
  A test uses both an explicit `harness.teardown()` call and an automated context manager `__exit__()` or fixture teardown hook. The second invocation detects that all servers are already stopped, executes immediately with zero delay, and raises no errors.

## Q&A

- **Q: Why is concurrent teardown necessary if servers already stop successfully sequentially?**
  A: While sequential teardown is functionally correct in clean conditions, its execution duration scales linearly ($O(N)$) with the number of servers. In test suites with 5+ servers, sequential teardown adds multi-second delays per test, compounding into significant CI test suite latency. Furthermore, sequential teardown is brittle: an error or hang on the first server halts or delays cleanup of subsequent servers. Concurrent teardown solves both performance and resilience problems.
- **Q: Will concurrent teardown introduce race conditions between servers?**
  A: Standalone MCP servers operate on independent network ports and separate background worker threads. Their lifecycles are decoupled from one another. Running their stop operations concurrently does not create cross-server dependencies, provided the registry's internal data structures and state transitions remain properly synchronized.
- **Q: How does this change affect existing tests and production runtime callers?**
  A: It does not require any code changes from callers. The public interface of `MCPServerRegistry.stop_all()` and harness `teardown()` / `close()` remains unchanged. Teardown remains a synchronous call that only returns when all parallel cleanup tasks have resolved or bounded timeouts have elapsed.
- **Q: What happens if a server fails or hangs during concurrent shutdown?**
  A: The teardown coordinator enforces a bounded join timeout on worker tasks and isolates exceptions on a per-instance basis. A failure or delay in one server cannot prevent other servers from being cleanly terminated. Any exceptions are collected and logged for debugging.
