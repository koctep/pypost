# PYPOST-1546: Stabilize flaky MCP process refresh neighbor isolation test (port bind)

## Goals

CI and local developers must trust parallel `make test` for process-mode MCP
refresh isolation. The neighbor/proxy isolation check must not fail intermittently
with “address already in use” when the same node passes alone. Stabilizing this
flake (same class as PYPOST-1541) restores confidence in the Test Gate Recovery
sprint signal and reduces noise that masks real regressions.

## User Stories

- As a **CI engineer**, I want
  `test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers`
  to pass reliably under parallel workers, so green builds reflect product
  behavior rather than lucky port timing.
- As a **developer**, I want the same test to pass in isolation and in the full
  suite, so I do not re-run flaky process-mode failures.
- As a **maintainer of MCP process tests**, I want batch ephemeral port
  reservation to reuse the held-bind approach from PYPOST-1541 so sibling flakes
  (PYPOST-1508, PYPOST-1552) can follow the same pattern.

## Definition of Done

- `tests/test_mcp_process_tool_refresh_repro.py::test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers`
  does not fail with address-in-use under parallel `make test` for this race class.
- A deterministic automated repro proves reserved ports stay exclusive against a
  reuse-addr thief until explicit release, then become bindable for the intended
  process-mode server handoff (Step 3 → Step 4).
- Process-mode suites that batch-allocate ports release the hold immediately
  before servers bind.
- No new unbounded waits; pytest timeouts remain explicit.
- Developer testing docs mention exclusive hold + release for process-mode ports.

## Task Description

**Problem:** Under parallel `make test`,
`test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers`
intermittently fails when a process-mode uvicorn worker cannot bind an ephemeral
loopback port (`EADDRINUSE` / errno 98). Neighbor start then times out
(`wait_for_state(..., 'running')` is False). The same test passes alone. Base
evidence and PYPOST-1541 classify this as allocate-then-release TOCTOU among
workers via `reserve_ephemeral_ports` / integer port handoff.

**In scope:** Stabilize batch ephemeral port reservation used by process-mode
MCP tests (hold exclusive binds; release immediately before child/server bind)
and apply that handoff in process-mode suites that allocate ports this way.

**Out of scope:** Changing production MCP listen semantics for end users;
disabling parallel workers; closing every related ticket’s distinct node id in
this change (remaining siblings stay follow-ups).

**Programming language:** Python.

## Q&A

- **Q:** Why is this business-facing debt rather than “just a flake”?
  **A:** Flaky parallel failures block sprint gates and hide real product bugs;
  process-mode refresh isolation is a shipped concurrency contract.
- **Q:** Why reuse PYPOST-1541’s held-bind idea instead of sleeping?
  **A:** Sleeps do not close the TOCTOU window; exclusive hold until release does.
  Process-mode cannot pass open sockets to uvicorn in-process like `LiveMCPServer`,
  so release-before-start is the handoff variant of the same pattern.
