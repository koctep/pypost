# PYPOST-952: Live out-of-process agent-UI MCP bridge

## Goals

[PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918) documented how
out-of-process MCP for UI actions must be packaged (dedicated entry, never
product `MCPServerImpl`). External agents and maintainers still need a
**runnable** sidecar that exposes click / fill / select / send-key over MCP
without conflating that catalog with collection HTTP request tools.

Business value: agents can compose **two** MCP servers — product request tools
on `MCPServerImpl` plus a separate agent-UI drive surface — following the
918 packaging contract with a shipped entry point.

Source: `ai-tasks/PYPOST-918/60-tech-debt.md` follow-up item 1.

## Programming Language

Python (`.cursor/lsr/do-python.md`); developer docs in English Markdown.

## User Stories

- As an **external MCP client operator**, I want a documented, runnable
  stdio (or equivalent) entry for UI-action tools so I can drive PyPost
  widgets out-of-process without adding tools to product MCP.
- As a **maintainer**, I want the bridge to wrap existing
  `pypost.agent.ui_actions` primitives so QTest logic is not duplicated.
- As a **product MCP consumer**, I want the request-tool catalog unchanged;
  UI drive remains on a dedicated server only.
- As a **CI maintainer**, I want automated tests proving the dedicated
  catalog and separation from `MCPServerImpl` without live external HTTP.

## Definition of Done

- Runnable packaging/entry for UI-action MCP separate from product HTTP tools
  (Jira acceptance).
- Dedicated MCP server exposes `ui_click`, `ui_fill`, `ui_select`,
  `ui_send_key` wrapping session-scoped ui_actions.
- No registration of UI-action tools on `MCPServerImpl`.
- Console script and/or `python -m` entry documented in `doc/dev/`.
- Tests green under `make test` / targeted pytest; lint clean on touched code.

## Task Description

**Problem:** PYPOST-918 closed the packaging **path** in docs only. Agents
still cannot spawn a supported out-of-process UI-action MCP sidecar.

**Business need:** Ship the live bridge so the documented path is executable,
preserving hard separation from product MCP HTTP tools.

### In Scope

- Dedicated agent-UI MCP module and stdio entry.
- Tool wrappers for existing ui_actions primitives.
- Packaging: `pyproject.toml` script + Makefile helper.
- Unit and stdio integration tests; dev docs.

### Out of Scope

- Mounting UI tools on `MCPServerImpl`.
- New ui_action primitives beyond existing four.
- Streamable HTTP variant for agent-UI MCP (stdio sidecar only in v1).
- Attach-to-already-running-desktop IPC (sidecar owns AgentAppSession).
- User-facing `doc/user/` docs.
- Jira transitions / commit (orchestrator).

## Functional Requirements

- FR1: Operators can run a packaged entry (`pypost-agent-ui-mcp` or
  documented equivalent) that speaks MCP over stdio.
- FR2: `list_tools` exposes exactly the four UI-action tool names aligned
  with ui_actions primitives.
- FR3: `call_tool` dispatches to `AgentAppSession` ui_* helpers.
- FR4: Product `MCPServerImpl` tool catalog remains free of UI-action names.
- FR5: Developer docs describe client wiring and separation from product MCP.

## Non-Functional Requirements

- **Separation:** Zero imports of agent-UI MCP from `mcp_server_impl.py`.
- **Discoverability:** Entry documented from `ui_actions.md` and dedicated
  dev doc.
- **Testability:** Default CI path uses offscreen Qt; stdio round-trip test
  marked `agent_e2e`.
- **Logging:** Tool calls logged at DEBUG without fill text (match ui_actions).

## Constraints and Assumptions

- Sidecar process hosts `AgentAppSession` (Qt + offscreen default).
- Qt UI calls run on the thread that created `QApplication` (no threadpool
  offload for widget drive).
- MCP Python SDK stdio transport (`mcp.server.stdio.stdio_server`).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Agent UI MCP sidecar | Stdio MCP server process |
| `AgentUiActionsMcpServer` | Tool catalog + dispatch |
| `AgentAppSession` | Qt lifecycle + ui_* convenience |
| `MCPServerImpl` | Product HTTP tools only (unchanged) |
| External MCP client | Spawns sidecar; composes with product MCP |

## Q&A

- Q: HTTP Streamable transport for agent-UI MCP?
  A: Out of scope for v1; stdio sidecar matches 918 packaging guidance.

- Q: Drive an already-open PyPost GUI?
  A: Out of scope; sidecar launches its own session (document as limitation).

- Q: Can tools be added to product MCP temporarily?
  A: No — forbidden by parent 918 acceptance.
