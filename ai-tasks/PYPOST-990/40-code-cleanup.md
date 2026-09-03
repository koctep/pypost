# PYPOST-990 Code Cleanup

## Review

- The existing `AgentUiActionsMcpServer` remains the single tool catalog for
  stdio and HTTP, so schemas and result envelopes do not diverge.
- HTTP lifecycle state is encapsulated in `AgentUiHttpServer`; the sidecar
  owns the exact Uvicorn thread and joins it with a five-second bound.
- `QtMainThreadDispatcher` executes directly on the owning Qt thread and uses
  a queued signal plus an event for HTTP workers. Exceptions and timeouts are
  returned to the MCP handler as the existing safe JSON error shape.
- The default `main()` call forwards only the historical spawn arguments unless
  `--http` is explicitly selected, preserving stdio and seed compatibility.
- New source and documentation lines satisfy the repository's line-length
  convention; no raw `print()` or unbounded wait was introduced.

## Verification

- Focused agent-UI, seed, and attach suites pass through `make test`.
- The optional live Streamable HTTP test passes through the slow-marker path.
- `make lint`, `make typecheck`, and `make verify-ai-tasks` pass.
