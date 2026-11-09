# PYPOST-1546: Technical Debt Analysis

## Shortcuts Taken

- Process-mode still cannot hand a pre-bound FD to the child uvicorn worker;
  `release()` then child bind leaves a short spawn-window race (much smaller
  than the former setup-window TOCTOU).
- Call sites must remember `ports.release()` / `reserve.release()` before
  start; forgetting fails loudly with EADDRINUSE on the held port rather than
  a silent flake against another worker.

## Code Quality Issues

- Some suites call `release()` inside a start loop (idempotent after the first
  call); a shared helper that releases once then starts N servers could be
  clearer.
- `allocate_tcp_port` / stub `ThreadingHTTPServer` paths still close before
  return (compat TOCTOU) — unchanged from PYPOST-1541 follow-ups.

## Missing Tests

- No multi-worker stress harness that forces dozens of concurrent
  `reserve_ephemeral_ports` + process starts (relies on suite parallelism +
  deterministic exclusive-hold repro).

## Performance Concerns

- Exclusive holds keep sockets open during collection/registry setup; cost is
  one FD per reserved port until `release()` — negligible for typical N≤10.

## Follow-up Tasks

| Item | Class | Notes |
| --- | --- | --- |
| PYPOST-1508 — same ephemeral port race class | NON-BLOCKER — pre-existing same class | Apply shared helper where ports are still allocate-then-release |
| PYPOST-1552 — process reconfigure EADDRINUSE under parallel | NON-BLOCKER — pre-existing same class | Confirm reconfigure suite inherits exclusive reserve + release |
| Migrate MCP integration stub HTTPServer ports to bind(0) or held sockets | Follow-up debt | Residual TOCTOU for stub listeners |
| Optional: FD inheritance of pre-bound sockets into MCP workers | Follow-up debt | Eliminates remaining release→bind spawn window |
