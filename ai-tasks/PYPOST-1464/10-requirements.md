# PYPOST-1464: Isolated Proxy Server Parity

## Goals

Operators choosing isolated execution must retain their existing proxy integrations and upstream
connection settings. An isolated proxy must forward to its configured upstream rather than
silently behave as a local collection server. This fulfills the approved MCP Process Reliability
sprint and the deferred proxy scope of
[PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439).

## Programming Language

- **Implementation language**: Python

## User Stories

- As an operator, I can start an existing proxy in isolated mode and discover and call upstream
  tools using the connection settings I saved.
- As an operator, I can retain existing authentication, transport selection, and request timeout
  behavior when choosing isolated execution.
- As an operator, I can stop or change one isolated proxy without disrupting neighboring servers
  or exposing authentication values in diagnostics.

## Definition of Done

1. An isolated proxy forwards supported MCP operations to the configured upstream, including tool
   discovery and invocation, instead of serving unrelated local tools.
2. The configured upstream address, existing transport selection, authentication headers, and
   request timeout retain their existing proxy meaning in isolated execution.
3. Both currently supported upstream transports, Streamable HTTP and legacy SSE, remain supported.
4. Existing variable resolution and secret-handling rules apply to proxy authentication settings;
   one server's credentials are not shared with another and diagnostics do not expose values.
5. Upstream failures remain visible as failures, with bounded connection/request waits according
   to existing timeout behavior; isolation does not silently report an unrelated successful result.
6. Existing start, stop, and configuration-change workflows retain proxy behavior and release
   the affected server's resources without disturbing neighboring integrations.
7. Automated checks demonstrate isolated forwarding and configuration parity, and existing local
   isolated-server and shared-execution proxy behavior remains covered by regression checks.

## Task Description

### Scope and Constraints

The task closes an execution-mode compatibility gap in existing proxy servers. It preserves
supported upstream operations and settings; it introduces no new transport, authentication scheme,
connection-pooling policy, or automatic recovery feature. Existing proxy limitations remain in
effect. Proxy configuration can contain sensitive credentials and must remain scoped to its owner.

Functional requirements are forwarding to the intended upstream, honoring saved connection
settings, preserving lifecycle behavior, and reporting connection failures accurately.
Non-functional requirements are bounded waits, secret-safe diagnostics, independent server state,
and compatibility with existing local servers and proxy configurations.

### Business Entities

- **Proxy server**: An operator-managed integration with identity, endpoint, execution choice,
  upstream connection settings, and lifecycle state.
- **Upstream server**: The configured source of MCP capabilities and results.
- **Connection settings**: Upstream address, supported transport, authentication headers, and
  timeout selected by the operator.
- **Neighboring integration**: Another server whose credentials and availability remain independent.

### Scenarios

An operator starts an isolated proxy with saved credentials and discovers/calls an upstream tool.
An operator selects the alternate supported upstream transport and retains equivalent forwarding.
An upstream is unavailable or too slow: the operation reports failure under the saved timeout.
An operator changes or stops a proxy while another integration continues serving independently.

## Q&A

**Why is this needed?** The approved sprint requires reliable process-worker parity. Operators
must be able to choose isolation without losing their working upstream proxy integrations.

**Are new upstream capabilities required?** No. Preserve the currently supported proxy behavior
and settings; architecture and internal message changes are decided in Step 2.
