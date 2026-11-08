# PYPOST-1469: Per-Worker Memory Ceilings and Spawn Admission for Isolated MCP Servers

## Goals

PyPost supports running standalone Model Context Protocol (MCP) servers in isolated execution mode,
where each server executes in a dedicated operating system process. This architecture provides crash
containment so that a fatal defect in a single tool integration does not terminate the host or peer
servers. However, each isolated process requires a non-trivial baseline memory footprint
(typically 30 to 50 megabytes of resident memory per process). In dense multi-server
deployments—such as ten or more concurrent servers running on workstations or enterprise
automation desks—spawning uncontrolled numbers of isolated workers or allowing a single
misbehaving tool integration to leak memory unbounded can exhaust host memory, causing
out-of-memory crashes of the entire host system or inducing severe operating system swap thrashing.

Today, there is no spawn admission control to enforce capacity boundaries on concurrent isolated
server instances or total estimated memory budget, nor are there per-worker memory ceilings to
detect and contain runaway memory growth. If an operator starts more servers than workstation
capacity allows, or if a tool integration accumulates memory without releasing it, the host system
is left vulnerable to uncoordinated operating system termination.

This task delivers configurable spawn admission controls and per-worker memory ceilings for isolated
MCP servers, addressing the tech debt identified in
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439) (TD-8):

1. Operators can define spawn admission limits (such as a maximum number of concurrent running
   isolated servers or an estimated aggregate memory budget) to prevent workstation memory
   exhaustion before new processes are launched.
2. When starting a server would exceed admission capacity, the request is cleanly refused with an
   actionable operator-facing error, while all existing running servers continue operating without
   disruption.
3. Operators can define per-worker memory ceilings with soft warning thresholds (for early alerting)
   and hard termination thresholds (to terminate runaway processes before they jeopardize host
   stability).
4. Continuous background monitoring observes isolated worker memory consumption, logs informative
   warnings when soft thresholds are breached, and gracefully terminates workers that breach hard
   thresholds, marking their status as failed.
5. Admission limits and memory ceiling terminations integrate harmoniously with automatic restart
   policies: admission refusals do not enter infinite restart loops, and memory-terminated workers
   obey restart backoff limits or remain failed if configured as non-retryable.
6. Lightweight shared-execution mode remains completely unaffected and backward-compatible.
7. All memory monitoring, admission decisions, and enforcement actions emit structured, secret-safe
   diagnostic records.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **enterprise automation operator**, I want to configure a maximum concurrent worker limit
  or total estimated memory budget for isolated MCP servers, so that dense automation desks do not
  over-commit host memory and cause workstation crashes.
- As a **desktop operator**, I want clear and actionable error feedback when a server start request
  is rejected due to admission limits, so that I understand why the server cannot start and know how
  to free capacity without disrupting existing running servers.
- As an **enterprise operator**, I want configurable per-worker memory ceilings with soft warning
  and hard termination thresholds, so that I receive early warnings when a server consumes excessive
  memory and have runaway processes terminated before they endanger the host.
- As a **system administrator**, I want runaway workers that exceed hard memory limits to be safely
  terminated and transitioned to a failed state, so that peer servers and the host application
  continue operating uninterrupted.
- As an **automation author**, I want admission rejections and memory-limit terminations to interact
  predictably with automatic restart policies, so that rejected starts do not spin in restart loops
  and memory-terminated workers do not repeatedly exhaust host memory.
- As a **desktop operator**, I want lightweight shared-execution mode to remain unaffected by
  isolated-mode memory ceilings, so that small trusted setups continue running with zero overhead.
- As a **security and operations engineer**, I want memory usage metrics, admission decisions, and
  ceiling enforcement events to be logged in a structured, secret-safe format, so that I can audit
  resource consumption without exposing sensitive tool configuration or variable data.

## Definition of Done

1. Configurable spawn admission controls allow operators to specify a maximum concurrent count of
   isolated server instances and/or an estimated total memory budget.
2. When starting an isolated server would exceed the configured admission limit, the start
   request is rejected safely without crashing, interrupting, or destabilizing any existing running
   servers.
3. Rejected start requests surface clear, actionable operator-facing diagnostic messages explaining
   the refusal reason (such as current running server count versus maximum allowed limit or
   estimated budget exhaustion) and how to resolve it.
4. Configurable per-worker memory ceilings allow operators to define soft warning thresholds and
   hard termination thresholds for isolated server resident memory usage.
5. Periodic monitoring observes the memory consumption of active isolated workers without degrading
   request-handling performance or user interface responsiveness.
6. When an isolated worker exceeds its soft memory threshold, an informational warning event is
   emitted with current usage and configured thresholds, while the worker continues serving.
7. When an isolated worker exceeds its hard memory threshold, the monitoring system triggers
   controlled worker termination, transitions the worker's status to failed with an operator-visible
   diagnostic, and frees its allocated resources.
8. Controlled termination of a memory-violating worker does not affect the host application or
   neighboring healthy servers.
9. Interaction with automatic restart policies is well-defined: admission denial stops further
   restart attempts for that instance, and workers terminated for exceeding hard memory ceilings
   obey restart backoff limits or are marked terminal if configured as non-retryable to avoid
   immediate re-exhaustion.
10. Shared-execution mode remains completely unaffected and backward-compatible.
11. Diagnostic logging and status reporting for memory monitoring, warnings, admission refusals, and
    terminations are structured and strictly secret-safe (no variables, secrets, or tool arguments
    exposed).
12. Developer documentation explains the expected per-worker memory footprint (30 to 50 megabytes
    baseline) and configuration guidelines for admission controls and memory ceilings.

## Task Description

### Problem and Scope

In isolated execution mode, each standalone MCP server runs within its own operating system process
boundary. While this prevents crashes in one tool integration from bringing down the host
application, each process requires an operating system baseline footprint (approximately 30 to 50
megabytes of resident memory per process). In dense desktop environments or automated test benches
where dozens of servers may be configured, unconstrained spawning can lead to host out-of-memory
situations.

Furthermore, poorly written tool integrations, memory leaks in underlying libraries, or large data
buffers can cause individual worker processes to balloon in memory over time. Without safeguards, a
single runaway worker can consume gigabytes of memory, inducing swap thrashing or triggering
operating system process kills that might terminate the host application or unrelated tasks.

Scope includes:

- Configurable spawn admission control governing the maximum concurrent isolated server instances
  and/or estimated aggregate memory budget.
- Safe rejection of spawn requests that exceed admission limits, returning clear operator messages
  without affecting active servers.
- Configurable per-worker resident memory ceilings including soft warning and hard termination
  thresholds.
- Background memory monitoring of active isolated workers that detects threshold crossings.
- Graceful escalation and termination of workers that breach hard memory limits, moving them to a
  failed lifecycle state.
- Coordinated interaction with the auto-restart recovery policy so that admission-refused or
  memory-terminated workers do not create destructive restart storms.
- Ensuring shared-execution mode remains unaffected.
- Secret-safe operational diagnostics, status messaging, and documentation of per-worker memory
  footprints.

Out of scope:

- Operating system containerization, cgroups, or kernel-level memory sandboxing.
- Dynamic runtime profiling or line-level memory attribution within tool implementations.
- Enforcing memory ceilings on shared-execution mode threads (threads share the single host address
  space and cannot have individual resident memory ceilings).
- Graphical UI dialog design for memory settings (configuration persistence and model controls
  follow existing configuration patterns; dialog layout is separate).

### Functional Requirements

- **FR1 (Configurable Spawn Admission Limits)**: Operators can configure admission limits for
  isolated execution, specifying a maximum number of concurrent running isolated server processes
  and/or an estimated aggregate memory budget. Sensible defaults allow unconstrained or safely
  bounded operation.
- **FR2 (Safe Admission Rejection)**: When a request to start an isolated server would cause running
  isolated servers to exceed the configured admission limit, the start request is immediately
  rejected. The rejection must not crash, pause, or interfere with already running servers.
- **FR3 (Actionable Admission Diagnostics)**: When admission is rejected, the system provides a
  clear, actionable operator-facing diagnostic message indicating why admission was refused (such as
  the current active server count relative to the configured ceiling) and suggesting remediation
  (stopping an inactive server or adjusting the limit).
- **FR4 (Configurable Per-Worker Memory Ceilings)**: Operators can configure per-worker resident
  memory ceilings for isolated servers, including an optional soft warning threshold and an
  optional hard termination threshold.
- **FR5 (Periodic Memory Usage Monitoring)**: The system periodically samples the resident memory
  consumption of all running isolated worker processes at a configurable or safe default interval
  without introducing noticeable latency into tool execution or user interface responsiveness.
- **FR6 (Soft Memory Ceiling Warnings)**: When a monitored isolated worker's resident memory exceeds
  the soft warning threshold, the system emits an operator-visible warning diagnostic indicating the
  server identity, current memory usage, and configured threshold, while allowing the worker to
  continue serving normally.
- **FR7 (Hard Memory Ceiling Enforcement and Escalation)**: When a monitored isolated worker's
  resident memory exceeds the hard termination threshold, the system initiates a controlled
  termination of that worker, transitions its status to failed with an explicit memory ceiling
  breach error, and reclaims its resources.
- **FR8 (Crash and Termination Isolation)**: Terminating a worker that exceeded its hard memory
  ceiling must never terminate the host application, drop connections to neighboring healthy
  servers, or corrupt shared registry state.
- **FR9 (Harmonious Auto-Restart Integration)**: When an automatic restart policy is enabled,
  admission rejection during a restart attempt must immediately halt the recovery cycle and mark the
  server failed rather than spinning in a retry loop. A worker terminated due to exceeding a hard
  memory ceiling must either observe the configured restart backoff limits or remain in a failed
  state to prevent immediate re-offense.
- **FR10 (Shared-Mode Compatibility)**: In shared-execution mode, servers run within the host
  process; spawn admission limits and per-worker process memory ceilings are gracefully bypassed or
  not applicable, preserving existing lightweight behavior without error.
- **FR11 (Secret-Safe Observability)**: All log events, status updates, and diagnostic messages
  concerning memory sampling, soft warnings, hard ceiling terminations, and admission rejections
  must strictly omit sensitive information, including environment variables, tokens, headers, and
  tool parameters.

### Non-Functional Requirements

- **NFR1 (Low Monitoring Overhead)**: Periodic sampling of worker memory must consume negligible CPU
  and memory resources, ensuring no perceptible impact on tool response latency or desktop UI
  smoothness.
- **NFR2 (Prompt Enforcement)**: Once a worker crosses a hard memory threshold, detection and
  initiation of termination must occur within a bounded observation window (for example, within a
  few seconds of sampling) before the host is starved of memory.
- **NFR3 (Fail-Safe Default Behavior)**: If memory ceiling features are disabled or unconfigured,
  isolated server execution must default to standard behavior without imposing artificial
  constraints or failures.
- **NFR4 (Cross-Platform Consistency)**: Memory measurement, admission control, and ceiling
  enforcement must function consistently across all supported desktop platforms (Linux, macOS,
  Windows) using standard platform memory metrics.
- **NFR5 (Deterministic Verification)**: Memory sampling, admission limits, and ceiling actions must
  be verifiable through automated tests with predictable bounds and mockable usage metrics, avoiding
  non-deterministic multi-minute waits.

### Constraints and Assumptions

- Memory ceilings measure resident memory of the isolated worker operating system process; shared
  libraries and kernel buffers are governed by standard operating system resident set accounting.
- In shared-execution mode, all servers share the host address space, making individual per-server
  resident memory isolation technically inapplicable.
- Operators accept that setting overly restrictive memory ceilings may prematurely terminate
  memory-intensive tool integrations; therefore, defaults should be disabled or generous.

### Main Business Entities

- **Spawn Admission Policy**: The rules and limits dictating how many concurrent isolated server
  processes may run simultaneously and the maximum estimated memory budget permitted before new
  server requests are declined.
- **Admission Decision**: The outcome of evaluating a server start request against active server
  capacity (accepted or rejected with diagnostic reason).
- **Per-Worker Memory Ceiling**: The configured resident memory boundaries for an individual
  isolated worker process, comprising an optional soft warning threshold and an optional hard
  termination threshold.
- **Worker Memory Snapshot**: A periodic measurement of an isolated worker's resident memory
  consumption captured by the monitoring system.
- **Memory Enforcement Action**: The response taken when a threshold is breached (logging a warning
  for soft thresholds, or initiating controlled termination and transition to failed for hard
  thresholds).
- **Isolated Server Instance**: An individual standalone MCP server running in its own operating
  system process with an assigned endpoint, lifecycle state, and dedicated memory footprint.

### User Scenarios

1. **Admission Limit Rejection Prevents Host Exhaustion**: An operator configures a maximum limit of
   five concurrent isolated servers. With five servers already running, the operator attempts to
   start a sixth server. The start request is immediately rejected with a message stating that the
   maximum concurrent worker limit has been reached. The five running servers continue serving
   requests without interruption.
2. **Soft Ceiling Warning Alerts Operator of Growth**: An operator configures a soft memory ceiling
   of 100 megabytes for isolated servers. During heavy data processing, one server's resident memory
   reaches 110 megabytes. The system logs an informational warning indicating the server exceeded
   its soft threshold. The server continues running and completing tool requests.
3. **Hard Ceiling Termination Protects Host from Runaway Leak**: An isolated server runs a tool
   integration that suffers from a severe memory leak, causing its resident memory to climb past its
   configured 200 megabyte hard ceiling. The monitor detects the breach, safely terminates the
   runaway worker process, transitions its status to failed with a message explaining the hard
   ceiling violation, and reclaims all associated resources. The host application and all other
   isolated servers remain stable and responsive.
4. **Auto-Restart Respects Admission and Memory Kill**: A running isolated server crashes while the
   cluster is at full capacity. The automatic restart policy attempts to restart it, but if
   admission capacity is unavailable, it marks the server failed rather than looping endlessly.
   For a server killed due to exceeding its hard memory ceiling, the system either applies backoff
   or terminates the recovery cycle to prevent immediate re-offense.
5. **Lightweight Shared Mode Operates Unconstrained**: An operator running in shared-execution mode
   starts multiple servers. Because shared mode runs in-process, process admission limits and
   per-worker memory ceilings do not restrict execution, ensuring existing low-overhead workflows
   continue uninterrupted.

## Q&A

**Q: Why are spawn admission controls needed if servers already run in isolated processes?**
A: Process isolation protects against fatal code faults, but each isolated process requires an
independent memory baseline (approximately 30 to 50 megabytes). In dense desks with dozens of
servers, spawning too many processes can exhaust workstation memory and cause host-wide
out-of-memory crashes. Admission control prevents overloading before processes are spawned.

**Q: What is the difference between a soft memory ceiling and a hard memory ceiling?**
A: A soft memory ceiling triggers an informational warning to alert operators of growing memory
usage while allowing the worker to continue serving normally. A hard memory ceiling triggers
controlled termination of the runaway worker process to prevent it from jeopardizing host stability.

**Q: How does admission rejection differ from a server crash?**
A: An admission rejection is a deliberate, clean refusal to start a new server because capacity
limits are reached. It immediately returns an actionable error message to the operator, does not
launch a subprocess, and does not destabilize existing running servers.

**Q: What happens if an operator does not configure any memory limits?**
A: Memory limits and admission controls are optional or default to safe or unconstrained boundaries,
ensuring backward compatibility with existing deployments.

**Q: Why don't memory ceilings apply to shared-execution mode?**
A: In shared-execution mode, all servers run within the single host process and share its memory
space. Individual threads cannot have their resident memory measured or capped by the operating
system independently without affecting the entire application.
