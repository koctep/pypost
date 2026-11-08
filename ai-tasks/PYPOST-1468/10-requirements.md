# PYPOST-1468: Active HEARTBEAT Watchdog and Failed State Transition for MCP Workers

## Goals

When Model Context Protocol (MCP) servers run in isolated execution mode, child worker processes
execute independently to handle tool execution, server lifecycle, and client communication.
Occasionally, worker processes can encounter deadlocks, infinite loops, unhandled blocking calls,
or resource exhaustion where the operating system process remains running, but the application
event loop is completely frozen.

Currently, although child worker processes can reply to heartbeat messages, the host supervisor
never actively initiates heartbeat probes. Because the supervisor relies exclusively on passive OS
process checks (such as process liveness or exit codes), it cannot detect when a worker process
has hung. The supervisor assumes the worker is healthy, leaving MCP client requests stalled
indefinitely and tying up valuable system resources (memory, sockets, file descriptors).

The goal of this task is to introduce an active, periodic heartbeat watchdog mechanism in the
supervisor. By actively probing isolated workers on a regular interval, detecting missing pong
responses beyond a configurable timeout threshold, terminating unresponsive workers cleanly, and
transitioning their status to failed, the supervisor can:
- Detect application-level worker deadlocks and freezes rapidly within a bounded timeframe.
- Protect system resources by terminating hung worker processes.
- Maintain high availability by transitioning unresponsive workers to an explicit failed state
  so automated recovery or supervisor alerting can take effect.
- Provide clear operational visibility and diagnostic auditability without affecting healthy peer
  workers.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **system operator**, I want the supervisor to actively monitor worker responsiveness via
  periodic heartbeat probes, so that deadlocks and silent freezes are detected rapidly and
  handled automatically without requiring manual intervention.
- As an **MCP client / user**, I want tool requests against frozen workers to fail fast and
  recover cleanly rather than hanging indefinitely and blocking my workflows.
- As a **monitoring system / observer**, I want immediate visibility when a worker becomes
  unresponsive (with clear diagnostics and an explicit transition to a failed state), so that
  health metrics, dashboards, and audit logs accurately reflect worker status.
- As an **automated recovery system / supervisor**, I want hung workers to be cleanly terminated
  and marked as failed, so that automated restart, recovery, or fallback workflows can proceed
  safely.

## Definition of Done

1. Active periodic heartbeat probing: The host supervisor actively dispatches periodic heartbeat
   probes to running isolated worker processes on a configurable cadence.
2. Responsiveness timeout detection: The supervisor monitors worker pong responses and flags a
   worker as unresponsive if no valid pong response is received within the configured timeout.
3. Clean termination of hung workers: When a heartbeat timeout occurs, the supervisor cleanly
   terminates the unresponsive worker process to prevent lingering or zombie processes.
4. Deterministic transition to failed state: Upon heartbeat timeout and worker termination, the
   supervisor updates the worker's operational state to a failed state.
5. Downstream recovery enablement: The transition to failed state triggers or allows downstream
   lifecycle handling (e.g. restart or cleanup) without leaving the worker in an orphaned state.
6. Configurable intervals and timeouts: Heartbeat probing interval, response timeout duration, and
   watchdog enablement are configurable with safe production defaults.
7. Backward compatibility: Existing healthy worker lifecycles, IPC message handling, and standard
   tool operations continue to function normally without regression.
8. Isolation containment: A heartbeat timeout and termination on one worker is strictly contained;
   it never crashes the supervisor, nor does it disrupt healthy peer workers.
9. Sanitized diagnostic logging: Heartbeat probe dispatch, pong reception, timeout expiration, and
   worker termination are logged with appropriate context (e.g. server identifier, PID, elapsed
   time) without exposing sensitive information.
10. Automated verification: Automated acceptance tests verify periodic probing, pong recognition,
    timeout detection, process termination, failed state transition, and isolation containment.

## Task Description

### Problem and Scope

In isolated execution mode, MCP server workers execute as separate child processes communicating
via an inter-process communication (IPC) channel. While worker processes implement handlers to
reply to heartbeat queries, the supervisor never transmits heartbeat probes. Consequently, if a
worker process encounters an unhandled deadlock, blocked thread, or CPU spin, the supervisor
cannot tell that the worker has stopped processing messages because the OS process remains alive.
This leaves user requests hanging indefinitely and retains occupied system resources.

The scope of this task includes:
- Implementing active periodic heartbeat probing initiated by the supervisor to running workers.
- Tracking probe dispatches and responses with a bounded watchdog timer.
- Detecting missed responses exceeding the configured timeout threshold.
- Safely terminating unresponsive worker processes upon heartbeat timeout.
- Updating worker status deterministically to a failed state.
- Enabling configurable probe intervals and timeout thresholds.
- Preserving supervisor stability and peer worker isolation.

Out of scope:
- Re-architecting underlying IPC transport channels or envelope serialization formats.
- Designing or modifying graphical user interface (GUI) dialogs or presentation views.
- Developing new automatic restart policies or backoff algorithms (managed by existing supervisor
  lifecycle workflows).
- Adding custom application-level watchdog logic inside child workers beyond responding to
  supervisor probes.

### Functional Requirements

- **FR1 (Active Heartbeat Probing)**: The supervisor must periodically dispatch heartbeat probe
  messages to running isolated worker processes at a configured interval.
- **FR2 (Pong Response Handling)**: The supervisor must register valid pong responses received
  from workers, updating last-seen timestamps and clearing pending timeout alerts.
- **FR3 (Timeout Detection)**: If a running worker fails to return a valid pong response within the
  configured timeout duration, the supervisor must classify the worker as unresponsive.
- **FR4 (Unresponsive Worker Termination)**: Upon detecting a heartbeat timeout, the supervisor
  must terminate the unresponsive worker process cleanly to reclaim operating system resources.
- **FR5 (Failed State Transition)**: When a worker is terminated due to a heartbeat timeout, the
  supervisor must deterministically transition the worker instance state to a failed state.
- **FR6 (Recovery Trigger)**: The transition to failed state must signal or integrate with existing
  lifecycle mechanisms to enable downstream recovery, alerting, or cleanup.
- **FR7 (Configurable Parameters)**: Heartbeat interval duration, response timeout duration, and
  watchdog enablement must be configurable with sensible, production-ready defaults.
- **FR8 (Failure Containment)**: A heartbeat timeout and subsequent termination of one worker must
  not crash the supervisor, corrupt shared state, or impact healthy peer workers.
- **FR9 (Lifecycle Coordination)**: Heartbeat probing must only occur while the worker is in an
  active/running state, and must cease cleanly when the worker is being stopped or has stopped.

### Non-Functional Requirements

- **NFR1 (Bounded Detection)**: Heartbeat timeout detection must occur within a predictable,
  bounded timeframe without indefinite delays or timer drift.
- **NFR2 (Low Resource Overhead)**: Heartbeat probing and watchdog monitoring must introduce
  negligible CPU, memory, and IPC overhead during steady-state operations.
- **NFR3 (Robustness & Fault Tolerance)**: Watchdog logic must handle process races gracefully
  (e.g., worker process exits independently while a probe or timeout is pending).
- **NFR4 (Observability & Diagnostics)**: Watchdog events (probe sent, pong received, timeout,
  termination) must emit clear, sanitized diagnostic logs with worker identifiers and elapsed
  durations.
- **NFR5 (Zero UI Regressions)**: This enhancement operates at the core process supervisor layer
  and requires zero modifications or regressions to UI components.
- **NFR6 (Cross-Platform Consistency)**: Watchdog timing, IPC messaging, and worker termination
  must operate reliably across Linux, macOS, and Windows.

### Constraints and Assumptions

- Implementation must be compatible with Python 3.
- Child worker processes already support responding to heartbeat requests with pong responses.
- The supervisor is the authoritative entity managing worker lifecycle and state transitions.
- Technical architecture choices (such as threading models, timer primitives, or termination
  signal sequences) are deferred to Step 2 (Architecture & Design).

### Main Business Entities

- **Host Supervisor**: The core orchestration component managing isolated worker lifecycles,
  monitoring process health, and initiating recovery.
- **Isolated Worker**: A dedicated child process running an MCP server instance, communicating
  with the host supervisor via IPC.
- **Heartbeat Probe**: An active query sent by the supervisor to test application-level
  responsiveness of the worker.
- **Heartbeat Pong**: The response returned by the worker confirming its event loop is actively
  servicing messages.
- **Watchdog Timer**: A monitoring mechanism tracking response latency and detecting expired
  deadlines.
- **Failed State**: An explicit worker lifecycle state indicating the worker is non-operational
  due to a failure, crash, or timeout.

### User Scenarios

1. **Scenario 1: Normal Heartbeat Steady State**:
   An isolated worker is running normally. The supervisor sends a periodic heartbeat probe. The
   worker responds with a pong. The supervisor updates the worker's responsiveness timestamp and
   resets the watchdog timer. The worker remains in the running state.
2. **Scenario 2: Worker Hang Detection and Termination**:
   An isolated worker becomes deadlocked or blocked in a non-responsive routine. The supervisor
   dispatches a heartbeat probe, but no pong response is received within the timeout limit. The
   watchdog detects the timeout, initiates clean process termination of the worker, records a
   diagnostic log, and marks the worker state as failed.
3. **Scenario 3: Downstream Recovery Invocation**:
   Following worker termination and transition to the failed state due to a heartbeat timeout,
   the supervisor triggers configured recovery workflows (such as notifying dependent clients or
   marking the instance eligible for restart).
4. **Scenario 4: Graceful Shutdown Lifecycle**:
   A running worker is stopped intentionally by an operator or host shutdown. The supervisor
   stops the heartbeat watchdog for that worker before or during termination, preventing false
   positive timeout detections while the worker is stopping.
5. **Scenario 5: Multi-Worker Isolation**:
   Multiple MCP workers run in isolated processes simultaneously. When one worker experiences a
   heartbeat timeout and is terminated and marked failed, other active workers continue servicing
   requests unaffected.

## Q&A

**Q: Why is an active heartbeat watchdog necessary if OS process monitoring already exists?**
A: OS process monitoring only detects process crashes or terminations (when the OS returns an exit
code). If a process hangs in an infinite loop, deadlocks on a thread lock, or blocks on unhandled
I/O, its OS process remains alive indefinitely. An active application-level heartbeat probe verifies
that the worker event loop is actively running and responsive.

**Q: Should the watchdog attempt automatic restarts or just mark the worker as failed?**
A: The watchdog is responsible for detecting unresponsiveness, terminating the hung worker to stop
resource leakage, and transitioning the worker state to failed. Downstream recovery (such as
restarts or client error notification) is handled by supervisor recovery workflows once the failed
state is established.

**Q: Are technical implementation details (e.g. QTimer, threading, IPC opcodes) specified here?**
A: No. In accordance with the Top-Down workflow methodology, technical designs, threading models,
and implementation schemas are strictly deferred to Step 2 (Architecture & Design).
