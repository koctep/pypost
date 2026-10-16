# PYPOST-1418: Concurrent Multi-Server Lifecycle Execution and Port Contention Testing

## Goals

In automated API testing, microservice integration, and AI-driven development workflows, users and automated systems often need to run multiple Model Context Protocol (MCP) server endpoints simultaneously. For instance, developers frequently run separate standalone MCP servers representing different microservices, environments, or API collections (e.g., authentication service, billing service, and inventory service) side-by-side within the same local PyPost workspace.

Prior tasks verified single standalone server lifecycle management in-process ([PYPOST-1410](file:///home/src/ai-tasks/PYPOST-1410/10-requirements.md)), collection variable resolution across single-server lifecycles ([PYPOST-1412](file:///home/src/ai-tasks/PYPOST-1412/10-requirements.md)), and live wire socket framing over single endpoints ([PYPOST-1416](file:///home/src/ai-tasks/PYPOST-1416/10-requirements.md)). However, in real-world environments, multiple standalone servers run concurrently and face severe multi-instance failure modes:
1. **Startup Race Conditions and Deadlocks**: When multiple standalone servers spin up simultaneously, concurrent initialization and port allocation can encounter race conditions or synchronization deadlocks.
2. **Variable Cross-Talk and State Leaks**: Multiple standalone servers often expose collections with identical or overlapping variable names (such as `base_url`, `token`, `timeout`, or `tenant_id`). Concurrently executing servers must maintain strict variable isolation so that modifications in one server's collection do not corrupt or bleed into another server's execution context.
3. **Dynamic Hot Reload under Load**: Modifying a collection's variables or configuration while other standalone servers are actively processing requests must not drop active connections on unaffected servers or deadlock the central registry.
4. **Port Contention and Collision Handling**: When two or more servers attempt to bind to the same network port, the system must detect the collision cleanly, prevent silent failures or process crashes, and report actionable errors or facilitate safe rebinding.
5. **Concurrent Teardown and Socket Hygiene**: Terminating multiple running servers simultaneously must release all network sockets, stop all background threads, and reclaim OS resources without leaving lingering sockets in `TIME_WAIT` or `EADDRINUSE` states that prevent immediate restarts.

The business goal of this task is to establish comprehensive automated test scenarios verifying concurrent startup, hot reload, variable isolation, port contention handling, and clean shutdown of multiple standalone MCP servers running simultaneously, guaranteeing system stability, isolation, and resource hygiene under high concurrency.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **API developer**, I want to run multiple standalone MCP servers concurrently within my workspace without port collisions or initialization race conditions, so that I can interact with multiple distinct API services simultaneously from my AI tools.
- As an **AI agent / automation client**, I want standalone MCP servers that share identical variable names (e.g., `base_url`, `api_key`) to remain strictly isolated, so that invoking tools on one server never leaks configuration values or causes cross-talk with another server.
- As an **integration engineer**, I want to dynamically update collection variables or reconfigure a single MCP server while other servers are actively processing traffic, so that configuration changes take effect without downtime, connection drops, or registry deadlocks on peer servers.
- As a **DevOps / platform operator**, I want the system to reliably detect and reject port conflicts with clear, structured diagnostics rather than crashing or silently hanging, so that configuration errors can be diagnosed and resolved immediately.
- As a **QA / automated test engineer**, I want concurrent multi-server test scenarios to execute deterministically within strict timeout limits and cleanly release all sockets and threads upon completion, so that CI test suites remain fast, reliable, and free of flaky failures.

## Definition of Done

This task is considered complete when:
1. Automated test scenarios verify concurrent startup of at least three standalone MCP servers running simultaneously on distinct allocated ports without race conditions, initialization deadlocks, or dropped events.
2. Variable isolation across concurrent servers is validated: multiple servers executing against identical or overlapping collection variable names (e.g. `base_url`) maintain completely independent runtime contexts without cross-contamination.
3. Dynamic hot reload under concurrent execution is verified: reconfiguring or updating collection variables for one server while peer servers are under active request execution succeeds cleanly without corrupting the registry or dropping peer connections.
4. Port contention handling is verified: attempting to start or reconfigure a server on an already-occupied port is cleanly detected, rejected, or rebound with actionable diagnostic error reporting without application crash or silent failure.
5. Concurrent multi-server teardown is verified: simultaneously terminating all running servers cleanly releases all network ports and background threads without lingering sockets or `EADDRINUSE` errors on immediate subsequent rebinding.
6. All tests adhere to repository testing contracts: execution completes within bounded timeouts (<30s per test), ensures deterministic synchronization without arbitrary sleeps, and guarantees zero leaked processes or dangling sockets.
7. Verification passes all project quality gates (`make verify-ai-tasks` and `make check`).

## Task Description

### Problem Statement

Developers and automated workflows increasingly rely on multiple standalone MCP servers running in parallel to expose diverse API collections as tools for AI models. In these multi-tenant and multi-server environments, standalone servers do not operate in isolation; they share the host operating system's networking stack, process space, and PyPost registry management layer.

When multiple servers operate concurrently, several failure modes emerge that single-server integration tests cannot detect:
- **Port Contention**: If multiple servers are assigned identical ports, or if a port is in the process of being released during a restart, binding collisions can cause uncaught socket exceptions, inconsistent registry states, or silent failures.
- **Variable Leakage / State Cross-Talk**: If runtime resolution or variable store lookup relies on shared mutable state, servers sharing variable names (such as `base_url` or `auth_token`) risk cross-contaminating each other's resolved values during concurrent tool invocations.
- **Hot Reload Registry Lock Contention**: Updating collection variables or switching environments on one server requires reconfiguring that server's runtime. If registry locking is coarse or flawed, a hot reload on Server A can block or crash active request handling on Server B.
- **Teardown Races & Socket Exhaustion**: Shutting down multiple servers concurrently can cause race conditions during thread joining and socket closure, resulting in lingering socket descriptors (`EADDRINUSE`) that break subsequent test runs or application restarts.

Automated test scenarios are required to systematically exercise and validate these concurrent lifecycle interactions.

### Scope

- **Concurrent Multi-Server Startup**:
  - Simultaneous initialization and startup of 3 or more standalone MCP servers across separate ports.
  - Validation of state transition consistency (all reach running status without deadlock or dropped signals).
- **Shared & Overlapping Variable Isolation**:
  - Deploying multiple concurrent servers configured with identical variable names but distinct values (e.g., Server 1 has `base_url = "https://alpha.example.com"`, Server 2 has `base_url = "https://beta.example.com"`).
  - Asserting that concurrent tool requests resolve exclusively to each server's specific runtime context without cross-talk.
- **Concurrent Hot Reloading**:
  - Updating variables or configurations on one active server while peer servers concurrently execute requests.
  - Validating that the updated server reloads cleanly while peer servers experience zero downtime or connection disruption.
- **Port Contention Detection & Mitigation**:
  - Simulating port collision scenarios (e.g., deliberate port collision across two servers, or starting a server on an externally occupied port).
  - Verifying graceful error detection, meaningful error status reporting, and safe fallback/rebinding behavior without crashing.
- **Concurrent Teardown & Resource Hygiene**:
  - Simultaneous shutdown of all active server instances.
  - Verifying all socket listeners close immediately and background execution threads terminate cleanly.
  - Verifying immediate port reusability without `EADDRINUSE` errors.

### Out of Scope

- Modifying the underlying JSON-RPC wire protocol specification or MCP wire schema (established in prior tasks).
- Implementing graphical user interface (GUI) dialogs, desktop menus, or UI styling for server management.
- External multi-host cloud deployment orchestration (testing is strictly local loopback / multi-instance on the host).

### Functional Requirements

- **FR1 (Concurrent Multi-Server Startup)**:
  - The test suite must verify simultaneous startup of at least 3 standalone MCP servers.
  - All servers must bind to their respective unique ports and transition to running state concurrently without race conditions, thread deadlocks, or lost status notifications.
- **FR2 (Shared and Overlapping Variable Isolation)**:
  - The system must enforce strict isolation when multiple servers run with identical or overlapping collection variable keys.
  - Concurrent requests dispatched to distinct servers must resolve only to their own respective collection variables without cross-talk, shared mutable cache leaks, or race conditions.
- **FR3 (Dynamic Hot Reload Under Concurrency)**:
  - The system must support reconfiguring or updating collection variables on a specific running server while other peer servers are actively processing requests.
  - The reconfiguration must commit without blocking peer server execution, corrupting the central registry, or dropping active connections on unaffected servers.
- **FR4 (Port Contention Detection and Mitigation)**:
  - When a standalone server attempts to bind to an already-bound or conflicting port, the system must detect the collision promptly.
  - The affected server must transition to a descriptive failure state with actionable diagnostic messages, without crashing the process, crashing the registry, or disrupting other running servers.
  - Subsequent rebinding to an available port must succeed cleanly.
- **FR5 (Concurrent Teardown and Socket Hygiene)**:
  - The system must support concurrent termination of all active standalone server instances.
  - All background threads must exit, all OS sockets must release immediately, and no zombie processes or dangling network descriptors must remain.
  - The released ports must be immediately re-bindable without encountering `EADDRINUSE` errors.

### Non-Functional Requirements

- **NFR1 (Bounded Execution Time)**:
  - All automated test scenarios must complete well within project testing time limits (<30 seconds per test module), ensuring no regressions in CI suite runtimes.
- **NFR2 (Deterministic Synchronization)**:
  - Tests must avoid arbitrary fixed sleeps (`time.sleep`) and instead utilize deterministic, bounded condition polling or event synchronization.
- **NFR3 (Thread Safety and Concurrency)**:
  - All registry operations and server lifecycle transitions must be thread-safe under concurrent access from multiple threads or asynchronous tasks.
- **NFR4 (Strict Resource Cleanup Hygiene)**:
  - Test fixtures must guarantee complete cleanup of all allocated sockets, threads, and temporary directories upon test completion (whether passing or failing), preventing cross-test pollution.

### Constraints and Assumptions

- Standalone MCP servers operate on local loopback network interfaces (`127.0.0.1`).
- Dynamic port allocation must select ephemeral ports that avoid collisions with active system services.
- The test harness must run cleanly in constrained Linux CI runner environments without special kernel privileges.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Standalone MCP Server** | An independent, self-contained service endpoint providing tool execution for a specific collection. | Server ID, allocated port, host address, lifecycle state (stopped, starting, running, failed), active collection ID. |
| **Server Registry** | Central manager responsible for tracking, starting, reconfiguring, and stopping standalone server instances. | Registered server list, active instance count, port allocation index, status change dispatcher. |
| **Collection Runtime Context** | The isolated execution environment containing collection-scoped variables, presets, and request definitions. | Collection ID, variable key-value mappings, active preset name, isolation boundary token. |
| **Port Contention Event** | An operational condition where a server attempts to bind to an address/port already occupied by another service. | Requested port, conflicting server/process identifier, error classification, diagnostic error message. |
| **Lifecycle Reconfiguration (Hot Reload)** | Dynamic update of a server's variables or configuration while maintaining service availability. | Target server ID, updated configuration payload, reconfiguration status (in-progress, committed, rejected). |
| **Lifecycle Teardown Batch** | Coordinated simultaneous shutdown of multiple active server endpoints. | Target instance IDs, shutdown start timestamp, socket release status, thread termination status. |

### User Scenarios

#### Scenario 1: Parallel Startup of Multiple Distinct Services
A user configures three standalone MCP servers representing an Authentication Service (port A), an Inventory Service (port B), and a Payments Service (port C). The user triggers a batch start. All three servers initialize and bind in parallel. All three report running status without race conditions, and each server becomes immediately accessible on its designated port.

#### Scenario 2: Overlapping Collection Variable Isolation Under Load
Two standalone servers run concurrently: Server A serves a development collection with `base_url = "https://dev.api.example.com"`, while Server B serves a staging collection with `base_url = "https://staging.api.example.com"`. High-frequency tool execution requests are sent concurrently to both servers. Server A consistently resolves requests to the dev URL, and Server B consistently resolves requests to the staging URL. No variable cross-talk or race conditions occur.

#### Scenario 3: Hot Reloading One Server During Concurrent Traffic
While Server A and Server B are actively processing tool execution requests, the user reconfigures Server A with updated variable values (e.g. updating an API key or timeout). Server A applies the updated configuration cleanly. During the reload, Server B continues serving client requests without interruption, dropped packets, or registry locking delays.

#### Scenario 4: Graceful Detection of Port Contention
A user accidentally configures Server C to bind to port A, which is already actively used by Server A. When Server C attempts to start, the system detects the port conflict. Server C transitions to a descriptive failed state explaining that port A is already in use. Server A continues running unaffected. When the user reconfigures Server C to an available port D and restarts it, Server C starts successfully.

#### Scenario 5: Rapid Concurrent Teardown and Port Reusability
The user issues a command to stop all running servers. All three servers receive termination signals concurrently. Background execution threads terminate, sockets close, and all resources are reclaimed. Immediately following shutdown, three new server instances bind to the exact same ports (A, B, C) and start successfully without encountering `EADDRINUSE` errors.

## Q&A

**Q: Why is concurrent multi-server lifecycle testing needed if single-server lifecycle and live wire tests already pass?**  
A: Single-server tests verify that one isolated server can start, exchange messages, and shut down. They cannot detect race conditions that only occur when multiple servers start simultaneously, cross-talk between collections sharing variable names, lock contention during hot reload of one server while another is executing, or socket reclamation races during batch shutdown.

**Q: How does this task differ from PYPOST-1416 (Wire IPC Stress Testing)?**  
A: PYPOST-1416 focused on wire-level packet framing, TCP chunk fragmentation, and stdio pipe buffer stress against a single standalone server instance. PYPOST-1418 focuses on multi-server orchestration, concurrent lifecycle state transitions, shared variable isolation, dynamic hot reload under peer load, and port contention prevention.

**Q: Does this task require modifying production code?**  
A: The primary goal is establishing the automated test scenarios and verification harness. If the test scenarios uncover real race conditions, deadlocks, variable leakage, or unhandled port collision bugs in the server registry or manager, targeted production fixes will be implemented to ensure the multi-server reliability contract is fulfilled.

**Q: How do we prevent test flakiness and port collisions with other test suites in CI?**  
A: Tests will use dynamic ephemeral port allocation (`allocate_tcp_port()`), explicit synchronization mechanisms (such as bounded polling and event signals) instead of hardcoded sleeps, and rigorous fixture teardown guarantees to ensure complete socket closure.
