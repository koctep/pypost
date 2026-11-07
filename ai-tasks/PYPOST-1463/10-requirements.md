# PYPOST-1463: Reliable Changes to Isolated MCP Servers

## Goals

Operators must be able to change a running isolated MCP server's configuration without losing
isolation or disrupting neighboring servers. A rejected change must leave the previously working
configuration usable, so operators can correct the change without restarting the host.

This closes the live-configuration gap identified in
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439), within the approved
MCP Process Reliability sprint goal.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an operator, I can change an isolated server's configuration while it is running, so that
  I can maintain tool integrations without restarting PyPost.
- As an operator, I can recover the last working configuration after a failed change, so that
  an invalid endpoint or unavailable resource does not leave my integration unnecessarily down.
- As an automation user, I can keep using neighboring servers during another server's change,
  so that maintenance of one integration does not interrupt unrelated work.

## Definition of Done

1. A valid change to a running isolated server takes effect under the same server identity and
   retains isolated execution after the change.
2. Successful changes work both when retaining the existing listening endpoint and when changing
   the listening endpoint. A change may briefly interrupt the affected server when required to
   reuse its endpoint; uninterrupted service for that affected server is not required.
3. A failed change does not become the accepted configuration. When the prior endpoint remains
   available, the previously working configuration serves requests again without a host restart.
4. If restoring the prior service also fails, the operator sees a truthful failure state and a
   useful diagnostic rather than a misleading running state or an unbounded wait.
5. Unrelated running servers remain operational and keep their own configurations throughout
   successful changes, rejected changes, and restoration attempts.
6. The operation finishes with only the accepted server configuration active. Abandoned attempts
   do not leave unmanaged servers or retain their listening endpoints.
7. Server status and reported configuration reflect the actual outcome; diagnostics do not
   disclose configuration secrets.
8. Automated acceptance checks demonstrate successful changes at the same and changed endpoints,
   failed-change restoration, peer continuity, and cleanup. Existing shared-execution behavior
   remains covered by regression checks.

## Task Description

### Problem and Scope

Isolated execution is available for starting standalone MCP servers, but live configuration
changes do not yet provide equivalent lifecycle behavior. This task makes those changes reliable
while retaining the chosen isolation boundary and preserving service on unrelated integrations.

Scope includes running isolated-server configuration changes, success and rejection outcomes,
restoration of prior service, resource cleanup, and accurate operator-visible status. Existing
shared-execution configuration changes must continue to work.

Out of scope are automatic crash restart policies, proxy forwarding parity, tool-list refresh
after collection edits, settings controls, memory limits, and active health monitoring. Those are
separate follow-ups to PYPOST-1439; this task does not expand their product behavior.

### Functional Requirements

- **FR1**: Apply a valid configuration change to the targeted running isolated server while
  retaining its identity and isolated execution.
- **FR2**: Support retaining or changing the target's listening endpoint.
- **FR3**: Reject unsuccessful changes and restore the previous working configuration when its
  required resources remain available; disclose a restoration failure when recovery is impossible.
- **FR4**: Keep unrelated server integrations operational and their configurations private.
- **FR5**: Expose truthful status and configuration after completion, rejection, or recovery.
- **FR6**: Release resources belonging to abandoned change attempts and replaced server instances.

### Non-Functional Requirements

- Configuration changes and recovery attempts must finish or report failure within finite
  lifecycle deadlines, using the product's existing startup and shutdown expectations.
- Configuration values and secrets remain scoped to their owning server; diagnostics must not
  expose secret values.
- Shared-execution behavior and existing server-management workflows remain compatible.

### Constraints and Assumptions

- The business purpose is established by the approved sprint goal and the parent task's explicit
  deferred reconfiguration scope; no additional product decision is needed for this follow-up.
- Restoring service cannot be guaranteed if an external actor takes the prior endpoint or the
  underlying service becomes unavailable. That outcome must be reported accurately.
- Brief interruption of the changed server is acceptable; peer-server availability is required.
- Architecture, concurrency coordination, and internal interfaces are decided in Step 2.

### Main Business Entities

- **Server instance**: An operator-managed integration with a stable identity, execution mode,
  listening endpoint, owned configuration, and lifecycle status.
- **Configuration change**: A requested replacement of one server's settings, with a success or
  rejection outcome.
- **Last working configuration**: The target server's accepted settings before a change attempt,
  used to restore service when the requested replacement fails.
- **Neighboring server**: Another running integration whose availability and settings must remain
  independent of the target server's maintenance.

### User Scenarios

1. An operator edits a running isolated server while keeping its address. The change succeeds,
   clients reconnect to the same integration, and peer servers keep serving requests.
2. An operator moves an isolated server to an available endpoint. The new endpoint serves the
   accepted configuration and the former endpoint is released.
3. A requested change cannot start. The previous working configuration resumes service and the
   operator sees why the requested change was rejected.
4. The change and subsequent restoration both fail because required resources are unavailable.
   The operator sees a failed state and can correct the problem without a hung host.

## Q&A

**Why is this needed?** Operators need reliable live configuration changes while preserving
service on failed changes. The approved sprint goal and PYPOST-1439's deferred scope establish
this business reason.

**Must the changed server remain continuously available?** No. Brief interruption may be needed
to retain its endpoint, but unrelated servers must remain operational.

**Does this include other process-mode parity gaps?** No. Proxy parity, collection tool refresh,
and automatic crash recovery remain separate Jira scopes.
