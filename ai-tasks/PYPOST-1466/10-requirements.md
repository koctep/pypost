# PYPOST-1466: Auto-Restart Policy with Exponential Backoff for Isolated MCP Servers

## Goals

Standalone Model Context Protocol (MCP) servers running in isolated execution mode protect the
PyPost host application and peer servers when an individual server terminates unexpectedly. Today,
any unexpected termination immediately places that server into a permanently failed state until an
operator manually restarts it. In enterprise and unattended automation environments where transient
faults (such as temporary upstream disconnects or transient resource exhaustion) can cause an
isolated server to exit, requiring manual intervention for every transient failure reduces tool
availability and interrupts automated workflows.

At the same time, blindly restarting a persistently broken server in a tight loop would waste host
resources and flood operator diagnostics. Furthermore, operators who prefer immediate failure
visibility without automatic retries must retain the existing default behavior.

This task delivers an opt-in automatic restart policy with progressive backoff for isolated MCP
servers, closing the lifecycle recovery follow-up identified in
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439) (TD-5):

1. Operators can keep the default behavior (immediate transition to a failed state on unexpected
   exit) or opt into automatic recovery for isolated MCP servers.
2. When automatic restart is enabled, an unexpectedly terminated isolated server is automatically
   restarted up to a configurable maximum number of attempts using a progressive (exponential)
   delay between attempts to prevent tight crash loops.
3. Once a restarted server remains healthy for a sustained operational window, its failure counter
   resets so future isolated transient faults can also recover.
4. If the server continues failing past the configured retry limit, automatic recovery stops and
   the server transitions to a terminal failed state until manual operator intervention.
5. Explicit operator lifecycle actions (stopping a server, reconfiguring a server, or shutting down
   all servers) immediately cancel any pending or in-progress automatic restart without hanging.
6. Automatically restarted servers preserve their latest accepted configuration, tool catalog,
   variables, secrets, and proxy settings without cross-server bleed.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **enterprise automation operator**, I want an opt-in automatic restart policy for isolated
  MCP servers, so that transient server crashes self-heal without manual intervention while
  deployments that prefer immediate failure keep the current default behavior.
- As an **enterprise automation operator**, I want automatic restarts to use a progressive backoff
  delay and a maximum retry limit, so that a persistently broken server does not spin in a tight
  crash loop or exhaust workstation resources, and clearly transitions to a failed state once
  retries are exhausted.
- As an **enterprise automation operator**, I want a server that recovers and stays healthy for a
  sustained period to reset its retry counter, so that an isolated transient fault hours later can
  still be recovered automatically.
- As a **desktop operator**, I want stopping, reconfiguring, or shutting down servers to cancel any
  scheduled automatic restart immediately, so that a server I explicitly stopped never comes back to
  life on its own or delays application shutdown.
- As an **automation author**, I want an automatically restarted server to resume serving with my
  latest configured tools, collection and environment variables, and proxy settings on the same
  endpoint, so that connected AI workflows continue using up-to-date definitions after recovery.
- As an **enterprise operator**, I want clear lifecycle status transitions and secret-safe
  diagnostic records for each crash, scheduled retry delay, recovery, and retry exhaustion event,
  so that I can monitor stability and troubleshoot recurring faults.

## Definition of Done

1. By default, automatic restart is disabled, and an unexpected termination of an isolated MCP
   server immediately transitions the server to the failed state with no retry attempts.
2. Operators can enable an opt-in automatic restart policy with configurable policy parameters,
   including maximum retry attempts, initial and maximum backoff delays, backoff progression, and
   the sustained healthy operation window required to reset the retry count.
3. When automatic restart is enabled and an isolated server exits unexpectedly after having started,
   the product schedules and executes automatic restart attempts with progressively increasing
   delays up to the configured maximum retry limit.
4. When a retry attempt succeeds, the server returns to the running state on its configured
   endpoint, preserves its latest accepted tools, variables, secrets, and proxy configuration, and
   resets its failure count once it remains healthy across the configured stability window.
5. When a server exhausts its configured retry attempts (or fails during a retry startup attempt
   after exhausting remaining retries), it transitions to the failed state and makes no further
   automatic restart attempts until an operator manually starts or reconfigures it.
6. Explicit operator stop, server reconfiguration, or cluster-wide shutdown immediately cancels any
   pending backoff wait or in-flight automatic restart within the bounded stop window and prevents
   the stopped or replaced server from restarting afterward.
7. Crashes and automatic restart cycles on one isolated server do not disrupt the host application
   or neighboring running servers, and never leak secrets or variable values into logs or peer
   servers.
8. Shared-execution mode and existing isolated-execution capabilities (live reconfiguration, live
   collection refresh, and proxy serving) continue to operate without regression.
9. Automated acceptance checks verify default immediate failure, opt-in recovery with progressive
   backoff, retry exhaustion to failed state, failure-counter reset after healthy operation,
   cancellation on explicit stop/shutdown, and state preservation across restarts.

## Task Description

### Problem and Scope

In isolated execution mode, each standalone MCP server runs within its own failure boundary. Today,
whenever an isolated server exits unexpectedly, the host records the server as failed and takes no
further action. While that matches the minimum baseline from PYPOST-1439, unattended and high-
density enterprise desks need optional self-healing for transient failures without risking unbounded
crash loops.

Scope includes:

- Providing a durable, opt-in automatic restart policy configuration for isolated MCP servers while
  keeping immediate failure as the default policy.
- Scheduling automatic restarts with progressive (exponential) backoff delays and a bounded maximum
  attempt count when a running isolated server terminates unexpectedly.
- Resetting the consecutive failure counter after a restarted server remains healthy for a
  configurable stability duration.
- Preserving the server's latest accepted runtime state (local tools, collection and environment
  variables, hidden/overridable variable rules, and upstream proxy configuration) across automatic
  restarts.
- Cancelling pending or active automatic restarts immediately upon explicit operator stop,
  reconfiguration, or cluster teardown.
- Recording clear, secret-safe operator status transitions and operational diagnostics for restart
  scheduling, successful recovery, cancellation, and retry exhaustion.

Out of scope are:

- Automatic restart for shared-execution (in-host) servers, which share the host failure boundary.
- Redesigning the graphical settings dialog (handled separately under PYPOST-1462).
- Active liveness ping watchdogs for hung-but-running servers (handled separately under
  PYPOST-1468).
- Per-server memory admission limits (handled separately under PYPOST-1469).

### Functional Requirements

- **FR1 (Opt-In Policy with Safe Default)**: Automatic restart is disabled by default so unexpected
  isolated-server exits immediately mark the server as failed. Operators can opt into automatic
  restart and configure maximum retry attempts, initial backoff delay, maximum backoff delay cap,
  backoff multiplier, and the healthy uptime window required to reset consecutive failure counts.
- **FR2 (Progressive Backoff Scheduling)**: When automatic restart is enabled and a running isolated
  server terminates unexpectedly, the product waits for a progressively increasing delay before each
  restart attempt, bounded by the configured maximum delay cap.
- **FR3 (Bounded Retry Exhaustion)**: If an isolated server fails consecutively across all allowed
  retry attempts, the product stops scheduling restarts and places the server into the failed state.
- **FR4 (Healthy Window Counter Reset)**: Once a restarted isolated server runs continuously and
  healthily for at least the configured healthy stability window, its consecutive retry counter
  resets to zero so subsequent transient failures receive a full retry budget.
- **FR5 (Runtime State Preservation Across Restarts)**: Every automatic restart uses the server's
  latest accepted configuration, refreshed tool definitions, refreshed collection and environment
  variables, secret-visibility rules, and proxy settings on the same configured listening endpoint.
- **FR6 (Immediate Cancellation on Operator Action)**: If an operator explicitly stops the server,
  reconfigures the server, removes/clears servers, or stops all servers while a backoff delay or
  restart attempt is pending, the pending restart is cancelled immediately and the server must not
  restart behind the operator's back.
- **FR7 (Initial Start Failure Distinction)**: If a server fails its initial operator-requested
  startup (for example, because its configured port is already in use or its configuration is
  invalid), the startup fails immediately with an operator-visible error rather than entering a
  background auto-restart loop.
- **FR8 (Neighbor Isolation and Secret Privacy)**: Automatic restart scheduling, backoff waiting,
  and recovery of one isolated server must not block or degrade peer servers, and diagnostic output
  must never expose secret variable values, headers, or tool payloads.

### Non-Functional Requirements

- **NFR1 (Crash-Loop Prevention)**: Backoff delays must strictly increase up to the configured cap
  so a repeatedly crashing server cannot saturate CPU or process-creation resources.
- **NFR2 (Bounded Stop Responsiveness)**: Cancelling a server that is waiting in a backoff window
  or mid-restart must complete within the existing bounded stop deadline (under a few seconds) so
  host shutdown never hangs waiting for a long backoff timer.
- **NFR3 (Deterministic Testability)**: The backoff and stability timing policy must support fast,
  deterministic automated verification within standard test timeout bounds without requiring multi-
  minute real-time waits.
- **NFR4 (Cross-Platform Consistency)**: Automatic restart, backoff scheduling, and stop
  cancellation must behave consistently across all supported desktop operating systems.

### Constraints and Assumptions

- Automatic restart applies only to isolated execution mode; shared execution mode does not have
  independent server process failure boundaries.
- Only unexpected exits of servers that had already reached a running state (or subsequent retry
  attempts in an active recovery cycle) trigger automatic restart; explicit operator stops and
  initial startup validation/binding rejections do not trigger automatic retries.
- Internal scheduling mechanisms and state representations are architectural decisions deferred to
  Step 2.

### Main Business Entities

- **Auto-Restart Policy**: The operator-configurable recovery rules governing whether unexpected
  isolated-server exits trigger automatic retries, how many retries are permitted, how delay grows
  between attempts, and how long a server must stay healthy to reset its failure count.
- **Recovery Cycle**: The sequence of one or more automatic restart attempts for a specific isolated
  server following an unexpected termination, tracking the current attempt number, next scheduled
  delay, and eligibility for further retries.
- **Healthy Stability Window**: The minimum continuous running duration after a recovery start
  required to consider the server stabilized and reset its consecutive failure counter.
- **Isolated Server Instance**: A standalone local or proxy MCP server running in isolated mode with
  its own identity, endpoint, lifecycle status, and private configuration/variable snapshot.

### User Scenarios

1. **Default Immediate Failure Preserved**: An operator runs isolated servers with default policy
   settings. One server crashes unexpectedly. The server immediately transitions to the failed state
   with zero automatic restart attempts, while peer servers continue serving normally.
2. **Transient Crash Self-Heals with Backoff**: An operator enables automatic restart (for example,
   up to 3 attempts). A running isolated server exits unexpectedly due to a transient fault. After
   the initial backoff delay, the product restarts the server with its latest refreshed tools and
   variables, returns it to the running state, and clients resume invoking tools on the same port.
3. **Persistent Crash Exhausts Retries and Stops**: A running isolated server with a 2-attempt
   policy begins crashing immediately on every restart. The product attempts recovery with
   increasing delays between attempts 1 and 2, and after the final failure transitions the server to
   the failed state and stops retrying.
4. **Healthy Operation Resets Retry Budget**: An isolated server with a 1-attempt policy crashes
   once, recovers automatically, and runs healthily past the configured stability window. When a
   second transient crash occurs later, the server still has its full retry budget and recovers
   again automatically.
5. **Operator Stop Cancels Pending Backoff**: An isolated server crashes and enters a backoff wait
   before its next retry. Before the delay elapses, the operator stops the server (or shuts down all
   servers). The pending retry is cancelled immediately and the server remains stopped.

## Q&A

**Q: Why is automatic restart opt-in rather than enabled by default?**
A: Keeping immediate failure as the default preserves backward compatibility with existing
deployments and diagnostics where operators expect a crashed server to remain failed until
inspected. Enterprises that run unattended or high-density setups can explicitly enable automatic
recovery.

**Q: Why combine exponential backoff with a maximum retry count and healthy reset window?**
A: Exponential backoff prevents rapid crash loops during short outages; the maximum retry limit
ensures permanently broken servers eventually stop consuming resources and alert the operator as
failed; the healthy reset window ensures long-running servers are not permanently penalized for a
single resolved glitch earlier in their lifecycle.
