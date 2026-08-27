# PYPOST-1196: Stabilize flaky MCP tool-update restart (port-busy race)

## Goals

Restore confidence in the automated suite for MCP server tool-set restarts.
Developers and CI must trust that changing the exposed MCP tool set reliably
leaves the manager listening again on the same host/port — without intermittent
`UiWaitTimeoutError` / `mcp_port_still_busy` / EADDRINUSE failures under
parallel `make test` load.

This debt was filed during PYPOST-1192 as a pre-existing NON-BLOCKER residual
flake after PYPOST-1178’s port-bindable wait landed.

## User Stories

- As a developer running `make test`, I need
  `test_update_tools_restarts_when_exposed_set_changes` to pass reliably under
  the full parallel suite so unrelated work is not blocked by port-busy races.
- As a maintainer of MCP server lifecycle, I need tool-set restart to wait until
  the prior binding is truly released (including when stop’s join times out
  under load) before rebinding the same port.
- As a sprint owner clearing Suite Failures Cleanup debt, I need this node green
  without changing sibling FILE_CAPS work (PYPOST-1194).

## Definition of Done

- `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
  passes under targeted `make test` and remains stable under parallel suite load
  (no intermittent restart timeout / EADDRINUSE after tool update).
- After an exposed-tool-set change that requires restart, the manager becomes
  listening again on the configured host/port within bounded waits, or failure
  remains visible via existing start-failed signaling — not a silent hang.
- Sibling Suite Failures Cleanup items remain out of scope (especially
  PYPOST-1194 FILE_CAPS).
- Top-down artifacts for this task are complete and the issue can close.

## Task Description

### Problem

`test_update_tools_restarts_when_exposed_set_changes` intermittently fails
during full parallel `make test` with
`UiWaitTimeoutError: MCP server did not restart after tool update
(timeout_s=10.0)`. Logs show `mcp_port_still_busy` then bind EADDRINUSE on
restart. The case usually passes alone and on re-run.

Confirmed flaky / pre-existing at base commit `18a4d9d1` (post PYPOST-1178)
during PYPOST-1192. Suspected residual port-busy race under parallel suite load.

### Functional requirements

1. When the exposed MCP tool set changes while the server is running, restart
   must leave the manager usable on the same host/port without intermittent
   EADDRINUSE from a still-busy prior binding.
2. Readiness waits after stop must remain time-bounded; if the port never frees,
   failure must stay visible (existing start-failed / wait errors), not hang
   forever.
3. The original regression node must assert restart readiness in a way that
   does not pass on a brief “thread started” blip before bind failure.
4. Do not reopen or redesign unrelated busy-port start signaling
   (`test_port_busy_emits_start_failed` / PYPOST-1113) or FILE_CAPS
   (PYPOST-1194).

### Non-functional requirements

- Fix covered by targeted `make test` on the MCP server-manager module (and
  full suite confidence for the flaky node).
- Changes stay minimal and local to MCP restart readiness / the flaky test
  contract.
- Programming language: **Python**.

### Constraints and assumptions

- Issue type: Debt; Medium; 3 story points.
- Sibling out of scope: PYPOST-1194 (FILE_CAPS). Done siblings: 1181 / 1193 /
  1195.
- Repro: `make test` (full suite; intermittent). Isolated usually green:
  `make test PYTEST_ARGS="tests/test_mcp_server_manager.py"`.
- PYPOST-1178 already added `_wait_until_port_bindable` between stop and start;
  this task addresses the residual flake under load.

### Main entities (business)

- **MCP server manager** — process that exposes HTTP tools; restarts when the
  exposed tool set changes.
- **Tool-set restart** — stop → wait until port bindable → start on same
  endpoint with the new tool set.
- **Port-busy race** — prior listener not released before same-port rebind under
  parallel suite / slow shutdown.
- **Automated restart regression** — suite node that proves restart reaches a
  usable listening state after an exposed-set change.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not only lengthen the test wait? | Failure logs show production `mcp_port_still_busy` then EADDRINUSE — the product restart path still races; test-only padding would mask, not stabilize, the lifecycle. |
| Is PYPOST-1178 incomplete? | It landed the wait gate; residual flake under parallel load remains (join timeout clearing a live thread, wait budget, weak `is_running` assert). |
| Is FILE_CAPS in scope? | No — PYPOST-1194 owns that. |
