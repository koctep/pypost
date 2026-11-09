# PYPOST-1508: Technical Debt Analysis

## Shortcuts Taken

- Process-mode still cannot hand a pre-bound FD to the child uvicorn worker;
  `release()` then child bind leaves a short spawn-window race (unchanged from
  PYPOST-1546; much smaller than the former mid-setup TOCTOU).
- Fix is call-site ordering only; no shared “upsert-all then release then
  start-all” helper was introduced.

## Code Quality Issues

- `tests/test_mcp_process_stress_10x.py` still calls `reserve.release()` inside
  a multi-server upsert/start loop (idempotent after first call) — same
  anti-pattern class as this ticket’s pre-fix isolation node. Out of scope
  for PYPOST-1508 node id; candidate follow-up.
- Other process suites may still release inside loops where N=1 (harmless) or
  where start immediately follows first upsert only.

## Missing Tests

- No multi-worker stress harness that forces dozens of concurrent
  `reserve_ephemeral_ports` + process starts (relies on suite parallelism +
  deterministic hold contracts).

## Performance Concerns

- Holding 10 exclusive sockets through all upserts adds negligible FD cost
  until the single release before starts.

## Follow-up Tasks

| Item | Class | Notes |
| --- | --- | --- |
| Process stress_10x release-inside-loop (same anti-pattern) | NON-BLOCKER — pre-existing same class | Align with hold-through-all-upserts |
| PYPOST-1552 — process reconfigure EADDRINUSE under parallel | NON-BLOCKER — pre-existing same class | Confirm reconfigure suite ordering |
| Optional: FD inheritance of pre-bound sockets into MCP workers | Follow-up debt | Eliminates remaining release→bind spawn window |
