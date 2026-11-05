# PYPOST-1439: Isolated Execution for Standalone MCP Servers

## Goals

PyPost runs standalone Model Context Protocol (MCP) servers so desktop operators and AI workflows
can expose tools over HTTP. Today those servers share the host application's process. That model
is efficient for small deployments, but enterprise environments often run ten or more servers at
once. At that density, a fatal fault in one server can take down the whole host, and heavy parallel
tool work can leave operators with a stalled UI and slower concurrent tool responses.

PYPOST-1438 evaluated isolation options and validated the current lightweight runtime under 10+
server stress. This task implements the follow-up business capability: operators must be able to
run standalone MCP servers in a strongly isolated execution mode so that:

1. A crash or fatal fault in one server does not abort the host or peer servers.
2. High-density concurrent tool work remains responsive without host-wide contention symptoms.
3. Each server keeps its own configuration and collection variables without cross-server bleed.
4. Stopping servers completes in bounded time so host shutdown and cluster teardown do not hang.
5. Operators who prefer the existing lightweight mode can keep it; isolation is an explicit choice
   for deployments that need stronger fault boundaries.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **enterprise automation operator**, I want each standalone MCP server to fail in isolation,
  so that a crash in one tool integration cannot terminate PyPost or stop my other active servers.
- As an **enterprise automation operator**, I want high-density multi-server workloads (10+ servers)
  to stay responsive under parallel tool use, so that the desktop host does not feel stalled when
  many servers work at once.
- As a **desktop operator**, I want to choose between lightweight shared execution and strong
  isolation for standalone MCP servers, so that small trusted setups stay lean while enterprise
  multi-tool setups get crash containment.
- As an **automation author**, I want each server's collection variables and secrets to remain
  private to that server under isolated execution, so that concurrent servers never leak or mix
  configuration values.
- As a **desktop operator**, I want stopping one server or shutting down the whole cluster to finish
  promptly, so that quitting PyPost or restarting servers never leaves the host hung waiting on a
  stuck isolated server.
- As a **QA / DevOps engineer**, I want automated checks that prove crash containment, variable
  isolation, and bounded stop behavior for isolated multi-server deployments, so that regressions
  are caught before release.

## Definition of Done

This task is considered complete when:

1. Operators can select an isolated execution mode for standalone MCP servers as a first-class
   product capability, while the existing lightweight shared mode remains available.
2. In isolated mode, a fatal failure of one standalone MCP server leaves the host application and
   all other running standalone MCP servers operational.
3. In isolated mode, concurrent work across 10+ standalone MCP servers does not produce host-wide
   contention symptoms that freeze or severely stall the desktop operator experience.
4. In isolated mode, each server resolves only its own configuration and collection variables;
   concurrent requests never observe another server's values.
5. Stopping a single isolated server or stopping all servers completes within a bounded operator-
   visible window; a stuck server cannot permanently hang host shutdown or cluster teardown.
6. Unexpected isolated-server exits are detectable to the operator (failed or stopped state is
   visible) without requiring a host restart.
7. Automated acceptance coverage demonstrates crash isolation, variable isolation under concurrent
   load, and bounded stop behavior for isolated 10+ server deployments.
8. Requirements, architecture, tests, cleanup, observability, tech-debt, and developer docs for
   this task are complete per the Top-Down workflow, and project quality gates pass.

## Task Description

### Problem Statement

Standalone MCP servers currently share the host process. PYPOST-1438 confirmed that the lightweight
model works under high-density stress when server code is well-behaved, and documented why that is
insufficient for enterprise fault boundaries:

- **Shared failure domain**: One fatal fault can abort the entire application and all peer servers.
- **Shared contention under density**: Parallel tool work across many servers can leave operators
  with UI sluggishness and serialized tool latency across the desktop host.
- **Incomplete product choice**: Operators cannot opt into stronger isolation when their deployment
  risk or density justifies the trade-off.
- **Variable privacy under isolation**: When servers run with stronger isolation, each server must
  still receive and retain only its own configuration and collection variables.
- **Shutdown reliability**: Operators must be able to stop isolated servers without indefinite host
  hangs, including when a server becomes unresponsive.

This task delivers the Phase 2 product outcome from the PYPOST-1438 evaluation: implement isolated
execution for standalone MCP servers so enterprise 10+ server deployments gain crash containment,
contention relief as an operator-visible outcome, per-server variable privacy, and orderly stop
behavior—without removing the lightweight mode for smaller setups.

### Scope

- Deliver operator-selectable isolated execution for standalone MCP servers alongside the existing
  lightweight shared execution mode.
- Ensure isolated mode provides crash containment for enterprise 10+ concurrent standalone MCP
  server deployments.
- Ensure isolated mode preserves per-server configuration and collection-variable privacy under
  concurrent load.
- Ensure start, health visibility, and stop of isolated servers are operable from the same
  operator-facing server management workflows used for lightweight mode.
- Ensure stop and host shutdown complete in bounded time with no unmanaged leftover servers, so
  the host does not hang.
- Provide automated acceptance coverage for the isolation, variable privacy, and bounded-stop
  outcomes above.

### Out of Scope

- Changing the MCP JSON-RPC protocol, tool schemas, or client wire formats.
- Rewriting third-party HTTP/ASGI server stacks or low-level network transports.
- Mandating isolated mode for every deployment; lightweight shared mode remains a valid choice.
- Container orchestration platforms, proprietary kernel drivers, or external process managers as
  the primary product control plane.
- Redesigning the MCP server registry catalog UX beyond what is needed to expose execution-mode
  choice and isolated lifecycle status.

### Functional Requirements

- **FR1 (Execution Mode Choice)**: Operators can choose lightweight shared execution or strong
  isolation for standalone MCP servers. The choice is durable as a product setting and applies to
  server start and lifecycle management.
- **FR2 (Crash Isolation)**: In isolated mode, fatal failure or unexpected exit of one standalone
  MCP server must not terminate the host application or other running standalone MCP servers.
- **FR3 (High-Density Continuity)**: In isolated mode, the product must support concurrent
  operation of at least 10 standalone MCP servers with independent tool request handling.
- **FR4 (Contention Relief Outcome)**: In isolated mode under concurrent multi-server load,
  operators must not experience host-wide freezes or severe UI stalls; peer servers and the
  desktop host remain usable with responsive concurrent tool handling.
- **FR5 (Variable and Configuration Isolation)**: In isolated mode, each server uses only its own
  configured values and collection variables. Concurrent requests must never observe another
  server's secrets or configuration.
- **FR6 (Lifecycle Visibility)**: Operators can start, stop, and observe status of isolated servers
  (including unexpected failure) through existing server management workflows.
- **FR7 (Orderly Bounded Shutdown)**: Stopping one isolated server or stopping all servers must
  complete within a bounded time. An unresponsive isolated server must not permanently block host
  shutdown or cluster teardown.
- **FR8 (Parity of Tool Serving)**: Isolated servers continue to expose the same MCP tool-serving
  behavior expected by clients; isolation must not change client-visible protocol semantics.

### Non-Functional Requirements

- **NFR1 (Enterprise Density)**: Isolated mode must remain operable for 10+ concurrent standalone
  MCP servers on supported desktop platforms without requiring a host restart to recover from a
  single isolated-server failure.
- **NFR2 (Stop Latency Bound)**: Operator-initiated stop of isolated servers must finish within a
  bounded window consistent with existing multi-server teardown expectations (on the order of a
  few seconds for a 10-server cluster under normal conditions).
- **NFR3 (Operator Clarity)**: Execution mode and per-server health/failure state must be clear
  enough that operators can diagnose a single failed server without restarting PyPost.
- **NFR4 (Cross-Platform Consistency)**: Isolation, variable privacy, and bounded stop behavior
  must be consistent across supported desktop operating systems.
- **NFR5 (Regression Safety)**: Lightweight shared mode remains available and continues to satisfy
  existing high-density stress expectations established under PYPOST-1438 unless an operator
  explicitly selects isolated mode.

### Constraints and Assumptions

- This work follows the Phase 2 adoption path documented after the PYPOST-1438 evaluation; Phase 1
  evaluation and 10+ stress baselines already exist.
- Operators may accept higher memory cost for isolation in exchange for crash containment; the
  product does not require isolation to match lightweight mode's memory footprint.
- Each isolated server must receive and use only its own configuration and collection variables;
  values must not bleed across concurrent servers.

### Main Business Entities

- **Execution Mode**:
  - *Description*: Operator-selected policy for how standalone MCP servers run relative to the
    host (lightweight shared vs strongly isolated).
  - *Business Attributes*: Selected mode, durability of preference, default for new deployments.
- **Isolated Server Instance**:
  - *Description*: One standalone MCP server running with a failure boundary separate from the
    host and from peer servers.
  - *Business Attributes*: Identity, listen endpoint, lifecycle state, configuration/variables
    owned by that server.
- **Server Lifecycle Operations (Business Role)**:
  - *Description*: Host-side business responsibility for starting, monitoring health of, and
    stopping isolated server instances, and for surfacing lifecycle status to operators.
  - *Business Attributes*: Managed isolated-server set, health/failure visibility, stop
    completion.
- **Per-Server Variable Context**:
  - *Description*: Configuration and collection values belonging to a single server instance.
  - *Business Attributes*: Key/value set, ownership by server identity, update visibility to that
    server only.
- **Cluster Teardown Event**:
  - *Description*: Operator or host request to stop one or many servers without hanging.
  - *Business Attributes*: Target set, completion deadline expectation, residual hang risk.

### User Scenarios

#### Scenario 1: Choose Isolation for an Enterprise Multi-Tool Desk

An enterprise operator enables isolated execution in settings, then starts twelve standalone MCP
servers for distinct corporate tools. All twelve become ready and serve tools. The operator
confirms the desktop host remains usable while tools run in parallel across the cluster.

#### Scenario 2: One Server Crashes Without Taking Down the Host

While twelve isolated servers are running, one server hits a fatal fault in a third-party native
dependency. Only that server transitions to a failed state. PyPost stays up, the other eleven
servers keep serving, and the operator sees the failed server without restarting the application.

#### Scenario 3: Variables Stay Private Under Concurrent Load

Ten isolated servers each have distinct collection variables (including secrets). One hundred
concurrent tool calls are distributed across the ten servers. Every response reflects only the
calling server's own values; no cross-server bleed occurs.

#### Scenario 4: Stuck Isolated Server Does Not Hang Host Shutdown

The operator stops all isolated servers during application quit. One isolated server becomes
unresponsive. Stop still completes within a bounded window: the host exits (or finishes teardown)
without an indefinite hang, and no unmanaged leftover servers remain from the operator's
perspective.

#### Scenario 5: Keep Lightweight Mode for Small Trusted Setups

A developer with two trusted local servers leaves lightweight shared execution selected. Behavior
matches the existing low-overhead model; isolation is not forced. The developer can switch to
isolated mode later when adding untrusted or high-density enterprise tools.

## Q&A

**Q: How does this task differ from PYPOST-1438?**  
A: PYPOST-1438 evaluated isolation trade-offs and proved the current lightweight runtime under
10+ server stress. PYPOST-1439 implements the operator-facing isolated execution capability so
enterprise deployments can opt into crash containment and contention relief.

**Q: Why is operator choice of execution mode a business requirement?**  
A: Isolation costs more memory and adds coordination overhead. Small trusted setups should keep
the lean shared model. Enterprise 10+ server desks that risk host crashes need an explicit,
durable way to opt into isolation without forcing that cost on every user.

**Q: What does "contention relief" mean for operators (not engineers)?**  
A: Under isolated mode with many busy servers, the desktop host and peer servers should remain
usable. Operators should not see the whole app freeze or serialize tool responses solely because
many servers are busy at once.

**Q: Why call out variable isolation separately from crash isolation?**  
A: Crash isolation protects availability. Variable isolation protects correctness and secrecy:
each server must continue to see only its own configuration and collection values under isolated
execution.

**Q: What does "orderly shutdown without hanging the host" mean in business terms?**  
A: When the operator stops servers or quits PyPost, teardown finishes in a predictable short
window. A stuck server must not leave the application waiting forever, and stop must leave no
unmanaged leftover servers from the operator's perspective.

**Q: Is isolated mode mandatory for all standalone MCP servers?**  
A: No. Lightweight shared mode remains valid. Isolation is required as an available product
capability for deployments that need stronger failure boundaries.
