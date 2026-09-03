# PYPOST-990 Technical Debt

## Retained scope

- The HTTP sidecar has no authentication, TLS, or remote authorization layer.
  This is intentional for the local agent-UI trust surface; documentation
  warns operators not to bind a shared interface without mutual trust.
- HTTP mode owns a spawned `AgentAppSession`. It does not provide an HTTP
  wrapper around the interactive desktop's attach host; attach remains the
  explicit stdio + AF_UNIX path.
- Port `0` is useful for tests and local launchers, but an external client
  needs the resolved listening log or a caller-selected fixed port.

## Follow-up decision

No new Jira debt issue is required for this ticket. Authentication/remote
exposure would change the trust model and needs a separately scoped security
design. Transport pooling and product MCP behavior remain outside PYPOST-990.
