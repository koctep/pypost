# PYPOST-1168: MCP-TM-8 — User documentation alignment

## Goals

MCP Client tab mode shipped in PYPOST-1165 through PYPOST-1170 (protocol picker entry,
draft tab shell, outbound headers, tool discovery, and interactive invoke). User-facing
guides still describe outbound MCP through the HTTP method **MCP** dropdown and do not
clearly separate **inbound** surfaces (MCP Servers, Expose as MCP Tool) from **outbound**
surfaces (MCP Client tab calling remote servers).

Readers following outdated docs cannot discover the real MCP Client workflow or understand
which UI areas serve agents versus which call upstream MCP servers.

## User Stories

- As a **developer testing a remote MCP server**, I want a user guide for the MCP Client
  tab (connect, list tools, invoke), so I can probe servers without writing JSON in an
  HTTP body.
- As a **new user**, I want `requests.md` to describe HTTP methods only, with a pointer to
  the MCP Client guide for outbound MCP, so I am not steered toward the legacy method path.
- As an **agent integrator**, I want `mcp-tools.md` to distinguish inbound tool exposure
  from outbound MCP Client usage, so I configure the correct surface for my workflow.

## Definition of Done

1. `doc/user/requests.md` no longer documents HTTP method **MCP**; it points to the MCP
   Client guide for outbound MCP.
2. A user guide page describes the MCP Client workflow (connect, list, invoke, headers).
3. `doc/user/interface.md` documents MCP Client as a workspace editor type alongside HTTP
   and WebSocket.
4. `doc/user/mcp-tools.md` clearly distinguishes inbound vs outbound MCP surfaces.
5. Automated contract tests guard the acceptance areas.

## Task Description

Docs-only alignment under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155). Depends on MCP-TM-1 …
MCP-TM-7 (PYPOST-1165 … PYPOST-1172). Architecture reference:
`ai-tasks/PYPOST-1164/20-architecture.md`.

### Out of scope

- Removing HTTP method **MCP** from the product (MCP-TM-6 / PYPOST-1171).
- Collections save/open for MCP Client profiles (MCP-TM-7 / PYPOST-1172).
- MCP Client context-aware hotkeys (PYPOST-1175).
- Developer architecture rewrites beyond cross-links in Step 8.

## Q&A

| Question | Answer |
| --- | --- |
| Why contract tests for prose? | Prevent regression when tab-mode MCP docs drift from shipped UX again. |
| Should docs mention legacy method MCP? | Brief redirect only — primary path is MCP Client tab; legacy path noted as transitional. |
