# PYPOST-1178: Stabilize flaky MCP server-manager restart test (EADDRINUSE)

## Goals

Continuous integration and local quality gates must give a trustworthy pass/fail
signal when the MCP server manager restarts after the exposed tool set changes.
Today,
`test_update_tools_restarts_when_exposed_set_changes` intermittently fails with
an address-already-in-use / port-still-busy condition after a restart, even when
the intended product behavior is correct. That false failure wastes engineer
time, undermines confidence in the suite, and can block unrelated work (as seen
once during PYPOST-1173 Step 6 full-suite validation; it passed on immediate
re-run).

This task restores reliable verification that updating the exposed tool set
triggers a clean restart and leaves the manager usable on its port, without
changing the business meaning of tool-set update or restart.

**Implementation language**: Python (reliability of MCP server manager restart
and supporting test helpers in the existing Python / Qt MCP suite; no new
runtime language).

## User Stories

- As a **developer or CI runner**, I want the exposed-tool-set restart test to
  pass consistently so that a green suite means the manager really restarted
  and rebound successfully after the tool set changed.
- As a **maintainer diagnosing flakes**, I want this known intermittent
  EADDRINUSE failure eliminated so unrelated task validation is not polluted by
  a pre-existing false negative.
- As a **user of the MCP server manager**, I want a tool-set change that
  requires restart to leave the local server ready to accept connections on the
  configured host/port, rather than failing because the previous instance’s
  port was not yet free.

## Definition of Done

- `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
  no longer fails intermittently with EADDRINUSE / port-still-busy after the
  manager restarts for an exposed-tool-set change.
- After a tool-set-driven restart, the manager is observed ready on its
  configured host/port within the existing time-bounded expectations of the
  suite.
- Existing uncommitted in-scope WIP is retained and landed with this task (not
  reverted); the delivered outcome remains restart readiness and port
  availability after tool-set-driven restart. Named WIP paths (scope only):
  - `pypost/core/qt/mcp_server.py`
  - `tests/helpers/mcp_live_server.py`
  - `tests/helpers/port_allocation.py` (new)
- Waits and readiness checks remain time-bounded; no unbounded delays.
- Sibling PYPOST-1113 (Done) remains out of scope except as related flake
  context; its signal-ordering wait for
  `test_port_busy_emits_start_failed` is not reopened or redesigned here.
- The flake is treated as pre-existing relative to PYPOST-1173 header-forwarding
  work; this debt item does not require revisiting that feature.

## Task Description

### Problem

When the MCP server manager restarts because the exposed tool set changed, the
named regression test sometimes fails because the configured port is still busy
(EADDRINUSE / bind failure). The failure was observed once under a full
`make test` run during PYPOST-1173 Step 6 and passed on immediate re-run,
confirming a flake rather than a deterministic product regression from that
task. Base commit noted at filing:
`df4148191b9227bb51d22619d451a2d0299c95ae`.

### Business need

Engineers need a stable regression check for “exposed tool set changed →
manager restarts and becomes usable again.” False failures erode trust in CI
and divert investigation away from real defects. Users also need tool-set
updates that restart the local MCP server to complete without leaving the port
unavailable.

### Scope

**In scope**

- Stabilize the exposed-tool-set restart path and its regression coverage so
  restart succeeds when the previous binding has not yet fully released the
  port.
- Land the existing uncommitted WIP listed under Definition of Done (do not
  revert).
- Keep readiness waits time-bounded and failure-visible when the port never
  becomes free within the allowed window.

**Out of scope**

- PYPOST-1113 busy-port start-failure signal-ordering flake (already Done);
  mention only as related context.
- Broader refactors of unrelated MCP server manager tests or features.
- Re-litigating PYPOST-1173 header-forwarding behavior (this flake was found
  during that work, not caused by it).
- Unrelated dirty tree items (for example `.DS_Store`, example JSON fixtures,
  other sprint artifacts) that are not part of the WIP listed above.

### Constraints and assumptions

- The intended business behavior—restart on exposed-tool-set change and resume
  serving—is already correct; the defect is intermittent failure when the port
  is not yet free after stop.
- Uncommitted WIP already present is an in-scope deliverable and constraint for
  this ticket: complete and land it; do not revert or replace it with a rewrite.
- Waits must remain time-bounded; no open-ended polling.
- Related debt origin: NON-BLOCKER follow-up 1 in
  `ai-tasks/PYPOST-1173/60-tech-debt.md`
  ([PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178)).

## Non-Functional Requirements

- **Reliability**: The named test must not fail intermittently under repeated
  suite runs when product restart behavior is correct.
- **Boundedness**: Any wait for port readiness after stop/restart must remain
  time-bounded with a clear outcome if the deadline is exceeded.
- **Isolation**: Ephemeral ports used by live MCP tests must not collide across
  concurrent or closely sequenced processes in a way that recreates this flake.
- **Scope discipline**: Changes stay limited to restart readiness and the named
  WIP helpers/tests supporting this debt item.

## Main Entities

- **MCP Server Manager**: Domain component that starts, stops, and restarts the
  local MCP server when the exposed tool set changes, and notifies observers of
  status.
- **Exposed tool set**: The collection of tools the manager currently publishes;
  changing that set can require a restart.
- **Tool-set-driven restart**: Stop-then-start cycle that must leave the server
  usable on the configured host/port.
- **Configured host/port binding**: Network endpoint the restarted server must
  reclaim before it is considered ready.
- **Restart regression test**: Automated check that updating the exposed tool
  set triggers restart and leaves the manager usable without EADDRINUSE.

## User Scenarios

1. **Single-test run**: A developer runs
   `test_update_tools_restarts_when_exposed_set_changes` alone; it passes and
   confirms restart after the exposed set changes.
2. **Full suite**: The same test runs inside `make test`; it does not flake with
   EADDRINUSE when the prior binding is slow to release.
3. **Unrelated task validation**: Maintainers running full-suite checks for
   other tickets (for example PYPOST-1173-style Step 6) are no longer blocked by
   this pre-existing restart flake.

## Q&A

**Why fix a flake that usually passes on re-run?**
Intermittent CI failures burn capacity and hide or distract from real
regressions; trustworthy gates are a product-quality requirement.

**Is the flake caused by PYPOST-1173 header forwarding?**
No. It was found during that task’s full suite; parent tech-debt notes it as
pre-existing / unrelated.

**Why land existing WIP instead of rewriting from scratch?**
The working tree already contains in-scope WIP toward restart readiness and
port availability for this flake; reverting would discard valid in-scope work,
and this task does not invent a rewrite.

**How does this relate to PYPOST-1113?**
PYPOST-1113 stabilized a different flake (signal-ordering wait in
`test_port_busy_emits_start_failed`). That work is Done and out of scope here
except as related context under the same MCP port-test reliability theme.

**What counts as success for the user-facing restart?**
After a tool-set change that requires restart, the local MCP server is again
ready on its configured host/port within normal time bounds, without bind
failures from a still-busy prior instance.
