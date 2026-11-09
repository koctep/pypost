# PYPOST-1541: Technical Debt Analysis

## Shortcuts Taken

- `allocate_tcp_port` / `free_port` still close the bound socket before return for
  backward compatibility. Call sites that only take an integer port (many
  `ThreadingHTTPServer` stubs in `test_mcp_server_integration.py`) retain the
  allocate-then-release window.
- `LiveMCPServer` bind retry uses a fixed attempt count (5) and 2s readiness
  timeout per attempt rather than adaptive backoff.

## Code Quality Issues

- `_DeadSocket` in the repro test is a narrow fake for fileno failure injection;
  acceptable for contract tests but not a general double.
- `EphemeralPortReserve` still allocates via integer `allocate_tcp_port` rather
  than holding a batch of open sockets.

## Missing Tests

- No multi-worker stress harness that forces dozens of concurrent
  `LiveMCPServer` starts (relies on suite parallelism + deterministic steal
  repro).
- Stub `ThreadingHTTPServer` paths in MCP integration tests were not migrated to
  bind-0 / held sockets in this ticket.

## Performance Concerns

- Worst-case `LiveMCPServer.start` can spend ~10s (5 × 2s) before raising; still
  bounded and under module timeout (120s for integration, 60s for repro).

## Follow-up Tasks

| Item | Class | Notes |
| --- | --- | --- |
| PYPOST-1546 — MCP process refresh neighbor isolation port bind | NON-BLOCKER — pre-existing same class | Reuse `allocate_bound_tcp_socket` / held reservation in process-mode harness |
| PYPOST-1508 — same ephemeral port race class | NON-BLOCKER — pre-existing same class | Apply shared helper where ports are still allocate-then-release |
| PYPOST-1552 — process reconfigure EADDRINUSE under parallel | NON-BLOCKER — pre-existing same class | Migrate to held bind or retry around candidate endpoints |
| Migrate MCP integration stub HTTPServer ports to bind(0) or held sockets | Follow-up debt | Reduces residual TOCTOU for stub listeners in `test_mcp_server_integration.py` |
| Optional: `EphemeralPortReserve` hold open sockets until yield ends | Follow-up debt | Stronger batch reservation for process stress suites |
