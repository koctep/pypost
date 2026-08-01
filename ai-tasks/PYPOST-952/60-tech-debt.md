# PYPOST-952: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: runnable stdio packaging entry (`pypost-agent-ui-mcp`,
`python -m pypost.agent.ui_actions_mcp`, `make run-agent-ui-mcp`) exposing
UI-action MCP tools separate from `MCPServerImpl`, wrapping ui_actions via
AgentAppSession, with unit + stdio integration tests and dev docs.

## Shortcuts Taken

- **Stdio-only v1** — no separate loopback Streamable HTTP port for agent-UI
  MCP (918 path mentioned both; stdio satisfies acceptance).
- **Sidecar owns AgentAppSession** — cannot attach to an already-running desktop
  PyPost; empty default data unless extended later.
- **Sync Qt dispatch on MCP thread** — no threadpool; relies on same-thread
  QApplication + `processEvents()` (correct for Qt, limits concurrent tool calls).
- **JSON ok/error TextContent** — errors returned in body rather than MCP error
  codes for UiActionError (agent-friendly parsing).

## Code Quality Issues

- Tool input schemas duplicated as dict literals in module — acceptable for four
  tools; extract shared builder only if catalog grows.
- No mypy coverage on `pypost/agent/` (project baseline excludes agent package).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Tool name constants | Covered |
| pyproject console script | Covered |
| MCPServerImpl exclusion | Covered |
| stdio list_tools subprocess | Covered (`agent_e2e`) |
| call_tool round-trip (click/fill) | Not covered — optional |
| Attach to running GUI | Out of scope |
| Streamable HTTP agent-UI MCP | Deferred |

**No timeout-marker blockers.**

## Performance Concerns

None for v1. Each sidecar spawns full Qt app; intended for agent-local use.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (Phase D ticketting)

1. **Streamable HTTP transport for agent-UI MCP**
   - Priority: Low
   - Separate loopback port mirroring MetricsServer pattern; compose with stdio
     clients that prefer HTTP
   - Files: `pypost/agent/ui_actions_mcp.py`, docs

2. **Attach sidecar to already-running PyPost desktop**
   - Priority: Medium when needed
   - IPC channel to existing QApplication instead of nested session
   - Files: new IPC layer + sidecar lifecycle

3. **call_tool integration tests (click/fill on fixture widgets)**
   - Priority: Low
   - Extend stdio or in-process memory transport tests beyond list_tools
   - Files: `tests/test_agent_ui_actions_mcp.py`

4. **Seed/collection injection for sidecar session**
   - Priority: Low
   - Allow agent-ui MCP to launch with agent e2e seed for realistic drive
   - Files: `ui_actions_mcp.py` CLI flags, agent_e2e helpers

## Deviations from Architecture

None material. Shipped stdio sidecar (Option A) as planned.

## Blocker Verdict

**SAFE TO CLOSE** — acceptance satisfied; follow-ups are optional enhancements.
