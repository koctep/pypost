# PYPOST-990 Requirements

## Business reason

The agent-UI MCP sidecar currently accepts MCP traffic only over stdio. Agents
that already run a local HTTP MCP stack cannot connect to the UI-action catalog,
and an HTTP request handler must not execute Qt widget operations from a worker
thread.

## User stories

- As an agent operator, I want to opt into a local Streamable HTTP endpoint for
  agent-UI tools so an HTTP MCP client can drive the sidecar.
- As an existing stdio client, I want the current default command and attach
  mode to keep their behavior and lifecycle unchanged.
- As a desktop user, I want every HTTP `call_tool` UI action to execute on the
  Qt application thread.
- As a maintainer, I want bounded startup and shutdown diagnostics for the
  optional HTTP listener.

## Functional requirements

1. Keep stdio as the default transport and preserve the existing four `ui_*`
   tools, schemas, server name, spawn path, and `--attach` path.
2. Add an optional Streamable HTTP entry selected by explicit CLI arguments;
   it must not bind a TCP port when the option is omitted.
3. Expose the agent-UI MCP catalog at the established `/mcp` path using the
   repository's shared Streamable HTTP route builder.
4. Support configurable HTTP host and port, with a deterministic default host
   and a caller-visible listening port for ephemeral-port use.
5. Marshal HTTP `call_tool` UI actions to the Qt application thread and wait
   for completion or failure with a bounded timeout.
6. Return the same MCP tool results and safe UI-action errors over stdio and
   HTTP; do not log filled text or request arguments containing user data.
7. Stop the HTTP listener and spawned `AgentAppSession` in all normal and
   exceptional exit paths.
8. Update developer and operator documentation with invocation, endpoint,
   ownership, trust, and shutdown behavior.

## Non-functional requirements

- HTTP is loopback-oriented by default and carries no authentication contract.
- The default stdio path must not acquire a background HTTP thread or require
  HTTP-only dependencies beyond those already used by the repository.
- Tests must be deterministic, bounded, and runnable through Make targets.
- Source and task documentation remain within the repository's line-length
  convention.

## In scope

- `pypost.agent.ui_actions_mcp` transport selection and lifecycle.
- A small Qt dispatch seam for cross-thread agent-UI calls.
- Focused unit/HTTP integration coverage and documentation.

## Out of scope

- Remote exposure, authentication, TLS, or browser CORS policy.
- Changes to product `MCPServerImpl`, product MCP catalogs, or desktop attach
  IPC protocol.
- Replacing the existing stdio transport or changing default CLI behavior.

## Acceptance criteria

- `pypost-agent-ui-mcp` remains stdio by default.
- An explicit HTTP option serves the same tools at `http://host:port/mcp`.
- HTTP `call_tool` crosses to the Qt main thread before invoking `UiDriveSession`.
- The HTTP listener and session have bounded cleanup.
- Agent-UI developer documentation describes both transports and trust scope.
