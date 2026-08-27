# PYPOST-1113: Stabilize port-busy start-failure test under load

## Goals

Continuous integration and local quality gates must give a trustworthy pass/fail
signal for MCP server manager startup failure handling. Today,
`test_port_busy_emits_start_failed` intermittently fails under system load even
when product behavior is correct: the test finishes checking outcomes before
every expected notification has arrived. That false failure wastes engineer
time, undermines confidence in the suite, and can block unrelated work (as seen
during PYPOST-1088 stress validation).

This task restores deterministic verification that a busy-port start reports
both failure and stopped status, without changing product start/stop behavior.

**Implementation language**: Python (test reliability within the existing
Python / Qt MCP server manager suite; no new runtime language).

## User Stories

- As a **developer or CI runner**, I want the busy-port start-failure test to
  pass consistently under normal and elevated load so that a green suite means
  the manager really reported failure and stopped status.
- As a **maintainer diagnosing flakes**, I want this known intermittent failure
  eliminated so stress runs of unrelated tasks are not polluted by a
  pre-existing false negative.
- As a **release engineer**, I want quality gates not to fail solely because
  two related startup notifications arrived in different order or at different
  times under load.

## Definition of Done

- `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed` waits
  until both expected outcomes are observed (start-failure notification and
  stopped status) before asserting on them.
- The test continues to verify that exactly one start-failure message is
  recorded, that the busy port appears in that message, and that the latest
  status is stopped.
- The test remains time-bounded and does not introduce unbounded waits or
  flaky fixed delays.
- Uncommitted in-scope WIP that already hardens this wait in
  `tests/test_mcp_server_manager.py` is retained and landed with this task
  (not reverted).
- No change to MCP server manager production start/stop behavior is required
  for this debt item.
- Sibling uncommitted work belonging to PYPOST-1178 is left untouched.

## Task Description

### Problem

`test_port_busy_emits_start_failed` checks that starting the MCP server on a
busy port emits a start-failure notification and a stopped status. Under load,
the test sometimes asserts on status history while that history is still empty,
producing intermittent `assert statuses` / empty-list failures. Discovery during
PYPOST-1088 Step 7 stress runs showed roughly 1/4–1/6 failure rate, including
on an unmodified baseline worktree — confirming a pre-existing flake unrelated
to PYPOST-1088.

### Business need

Engineers need a stable regression check for “port busy → start failed and
stopped.” False failures erode trust in CI and divert investigation away from
real defects.

### Scope

**In scope**

- Harden the busy-port start-failure test so assertions run only after both
  expected notifications have been observed.
- Land the existing uncommitted WIP in `tests/test_mcp_server_manager.py` that
  already extends the wait accordingly (do not revert).

**Out of scope**

- Changes to MCP server manager production code paths for bind/start/stop.
- Broader refactors of other MCP server manager tests.
- Uncommitted sibling sprint work for PYPOST-1178:
  `pypost/core/qt/mcp_server.py`, `tests/helpers/mcp_live_server.py`,
  `tests/helpers/port_allocation.py` (mention only; do not edit).
- Reopening PYPOST-716 (macOS segfault in the same test); that was a different
  symptom and is already Done.

### Constraints and assumptions

- Product behavior (emit start-failed and stopped status on busy port) is
  already correct; the defect is incomplete synchronization in the test.
- Waits must remain time-bounded; no unbounded delay.
- Related debt origin: NON-BLOCKER follow-up in
  `ai-tasks/PYPOST-1088/60-tech-debt.md`.

## Non-Functional Requirements

- **Reliability**: The named test must not fail intermittently under repeated
  suite or stress runs when product behavior is correct.
- **Determinism**: Pass/fail must not depend on which of two related
  notifications arrives first under load.
- **Boundedness**: Waits must remain time-bounded; no open-ended polling.
- **Isolation**: Fix is limited to this test’s observation of outcomes; no
  cross-test state changes.

## Main Entities

- **MCP Server Manager**: Domain component that starts/stops the local MCP
  server and notifies observers of start failure and running/stopped status.
- **Busy-port start attempt**: Scenario where start is refused because the
  target port is already in use.
- **Start-failure notification**: Observer-facing signal that start did not
  succeed, including context such as the port.
- **Status notification**: Observer-facing signal that the manager is running
  or stopped.
- **Busy-port regression test**: Automated check that both notifications occur
  for a busy-port start and that status ends stopped.

## User Scenarios

1. **Single-test run**: A developer runs
   `test_port_busy_emits_start_failed` alone; it passes and confirms failure
   message content plus stopped status.
2. **Loaded suite / stress**: The same test runs inside a larger or repeated
   suite under machine load; it still waits for both outcomes and passes
   without empty-status assertions.
3. **Unrelated task stress validation**: Maintainers re-running PYPOST-1088-style
   multi-module stress commands are no longer blocked by this pre-existing flake.

## Q&A

**Why fix a “test-only” race?**
False CI failures burn capacity and hide or distract from real regressions;
trustworthy gates are a product-quality requirement.

**Is production MCP start/stop broken?**
No. Baseline stress runs show correct emissions; the test sometimes checks
outcomes before both notifications have arrived.

**Why land existing WIP instead of rewriting?**
The working tree already contains matching wait hardening for this flake;
reverting would discard valid in-scope work.

**Why exclude PYPOST-1178 files?**
Those edits belong to a sibling sprint issue; touching them would mix scopes
and risk incorrect attribution.

**How does this relate to PYPOST-716?**
PYPOST-716 fixed a macOS segfault in the same test; this ticket addresses a
separate Linux signal-ordering flake.
