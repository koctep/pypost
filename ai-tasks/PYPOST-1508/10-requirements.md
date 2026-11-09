# PYPOST-1508: Stabilize flaky MCP process-mode concurrent variable isolation test

## Goals

CI and local developers must trust parallel `make test` for process-mode MCP
variable isolation under concurrent load. The concurrent isolation check must
not fail intermittently with “address already in use” when the same node passes
alone. Closing this flake (same class as PYPOST-1541 / PYPOST-1546) restores
confidence in the Test Gate Recovery sprint signal and reduces noise that masks
real regressions.

## User Stories

- As a **CI engineer**, I want
  `test_process_mode_variable_isolation_under_concurrent_load` to pass reliably
  under parallel workers, so green builds reflect product behavior rather than
  lucky port timing.
- As a **developer**, I want the same test to pass in isolation and in the full
  suite, so I do not re-run flaky process-mode failures.
- As a **maintainer of MCP process tests**, I want the isolation suite to finish
  applying the exclusive hold + single release-before-start pattern already
  introduced by PYPOST-1546, with no remaining mid-setup release gap.

## Definition of Done

- `tests/test_mcp_process_isolation_repro.py::test_process_mode_variable_isolation_under_concurrent_load`
  does not fail with address-in-use under parallel `make test` for this race
  class.
- A deterministic automated repro proves multi-server setup keeps exclusive
  holds through **all** upsert steps until a **single** release immediately
  before starts (Step 3 → Step 4).
- Any remaining call-site gap vs PYPOST-1546 (early `release()` inside the
  upsert/start loop) is closed for this node.
- No new unbounded waits; pytest timeouts remain explicit.
- Developer testing docs note hold-through-all-upserts for multi-server
  process-mode setups (PYPOST-1508 closeout).

## Task Description

**Problem:** Under parallel `make test`,
`test_process_mode_variable_isolation_under_concurrent_load` intermittently
fails when a process-mode uvicorn worker cannot bind an ephemeral loopback port
(`EADDRINUSE` / errno 98). Runner start then times out
(`mcp_process_runner_start_failed` / STARTED timeout 15s;
`AssertionError` in the collection integration harness). The same test passes
alone. Base evidence and sibling tickets classify this as port contention among
workers.

**Context:** PYPOST-1546 already added exclusive hold + `release()` to process
suites including `isolation_repro`. This ticket verifies that coverage and
completes any remaining gap so the named node is stable.

**In scope:** Verify and finish hold/release ordering for the concurrent
variable-isolation process-mode test; document closeout.

**Out of scope:** Changing production MCP listen semantics; disabling parallel
workers; closing every sibling flake ticket in this change.

**Programming language:** Python.

## Q&A

- **Q:** Why is this business-facing debt rather than “just a flake”?
  **A:** Flaky parallel failures block sprint gates and hide real product bugs;
  process-mode variable isolation is a shipped concurrency contract.
- **Q:** Why not only re-run until green?
  **A:** Solo re-run already passes; the defect is parallel-worker port timing.
  Exclusive hold through full multi-server setup, then one release before start,
  closes the window without sleeps.
