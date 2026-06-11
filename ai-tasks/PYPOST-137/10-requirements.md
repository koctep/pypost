# PYPOST-137: Document MCP active-environment binding and observability

## Goals

PyPost MCP resolves environment variables from the **currently selected** environment. When
operators switch environments while agents are connected, subsequent tool calls silently use
new variable values. Agents may assume stable context across a session — this is a product
clarity and operability gap from PYPOST-16 tech-debt follow-up.

The business goal is to make this behavior **explicit** for operators and developers, add
lightweight observability when environment identity changes during an active MCP session, and
confirm that tool execution already reads the latest environment at call time (no stale cache).

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **PyPost operator**, I want documentation that MCP tools follow the active
  environment selection, so I know switching envs affects connected agents.
- As an **AI agent operator**, I want to understand that environment variables may change
  mid-session if the PyPost user switches environments, so I do not misattribute failures.
- As a **developer**, I want a log/metric when the active environment changes while MCP is
  running, so I can correlate agent surprises with operator actions.

## Definition of Done

- [x] Developer and user docs describe active-environment binding and agent implications.
- [x] When environment **identity** changes while MCP server is running, PyPost logs
  `mcp_active_env_changed` and increments `mcp_active_env_changes_total`.
- [x] Same-environment variable edits do not emit the env-change event (identity unchanged).
- [x] Existing per-call variable supplier behavior verified by tests (no regression).
- [x] No MCP spec rebuild; pragmatic scope only.

## Task Description

Source: PYPOST-16 tech-debt — "Single Environment: server uses active env; switching in UI
may surprise agents."

In scope: documentation, optional metric/log on env identity change while MCP running,
verification of call-time env resolution.

Out of scope: per-agent environment locking, MCP protocol notifications to clients, multi-env
MCP servers.

## Q&A

| Question | Answer |
| --- | --- |
| Should agents be notified via MCP? | No — out of scope; document behavior instead. |
| Does switching env restart MCP? | May restart when moving between MCP-enabled envs; variables always follow selection. |
| Variable edit vs env switch? | Only identity change while MCP running triggers the new event. |
