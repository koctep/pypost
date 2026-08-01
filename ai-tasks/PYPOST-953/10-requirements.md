# PYPOST-953: Assert product MCP catalog excludes UI tools

## Goals

PYPOST-918 closed with doc-token locks and a documented packaging path that
forbids mounting UI-action tools on product `MCPServerImpl`. PYPOST-952 then
shipped a dedicated agent-UI MCP sidecar with its own tool catalog. Maintainers
still need a **runtime guard** in the canonical product MCP test module so a
future change cannot silently register `ui_click`, `ui_fill`, `ui_select`, or
similar drive tools on the product server without CI catching it.

Business value: harden the no-mixing constraint beyond Markdown substrings;
protect external MCP consumers who expect collection HTTP tools only on product
MCP.

Source: [PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918) follow-up
item 2 (runtime assert). Parent packaging: [PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918);
sidecar delivery: [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952).

## User Stories

- As a **maintainer**, I want an automated test on `MCPServerImpl.list_tools()`
  that fails if UI drive tool names appear, so product MCP cannot regress into
  mixing surfaces.
- As a **contributor**, I want the guard in `test_mcp_server_impl.py` (canonical
  product MCP tests), so I discover the rule where other catalog tests live.
- As a **product MCP consumer**, I want CI to enforce that my tool catalog stays
  HTTP-request tools only, independent of agent-UI sidecar packaging.

## Definition of Done

- A unit test in `tests/test_mcp_server_impl.py` asserts `MCPServerImpl` tool
  names do not overlap agent UI MCP tool names (`ui_click`, `ui_fill`,
  `ui_select`, `ui_send_key`) and do not include `ui_*`-prefixed tools.
- Test fails with a clear message if any such name is registered.
- No change to product MCP runtime behaviour (guard only).
- Developer docs reference the guard and how to run it.
- Unticketed follow-ups (if any) recorded only in `60-tech-debt.md`.

Acceptance (from Jira): **Test fails if MCPServerImpl exposes
ui_click/ui_fill/ui_select-style tools.**

## Task Description

**Problem:** PYPOST-918 deferred a runtime catalog assert as optional hardening
(PYPOST-953). Doc locks and the PYPOST-952 sidecar exist, but product MCP tests
did not yet assert the separation at runtime in the canonical impl test module.

**Business need:** Close the deferred guard so accidental UI-tool registration
on `MCPServerImpl` is caught in CI before it reaches external agents.

### In Scope

- Runtime unit test on `MCPServerImpl.list_tools()` catalog names.
- Cross-reference in developer docs / testing guide.
- ai-tasks artifacts for PYPOST-953.

### Out of Scope

- Changing `MCPServerImpl` registration logic (already correct).
- Live MCP integration or GUI tests.
- Removing or rewriting PYPOST-952 sidecar tests (sibling coverage OK).
- User-facing docs (`doc/user/`).
- Git commit or Jira transitions (orchestrator).

## Functional Requirements

- FR1: Test detects overlap with canonical agent UI tool name set.
- FR2: Test detects any `ui_*`-prefixed tool name on product catalog.
- FR3: Test lives in `tests/test_mcp_server_impl.py`.
- FR4: Failure message identifies offending tool names.

## Non-Functional Requirements

- **Speed:** No live MCP session, Qt GUI, or network — `list_tools()` only.
- **Stability:** Use shared `AGENT_UI_MCP_TOOL_NAMES` constant from sidecar
  module as single source of truth for the four primitives.
- **Timeout:** Module `pytestmark` already applies (`timeout(60)`).

## Constraints and Assumptions

- Python + pytest per project conventions.
- Production code already excludes UI tools; this is test-only hardening.
- PYPOST-952 `tests/test_agent_ui_actions_mcp.py` may retain a sibling assert;
  this ticket owns the canonical `test_mcp_server_impl.py` guard.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| `MCPServerImpl` | Product MCP server; exposes collection HTTP tools only |
| `AGENT_UI_MCP_TOOL_NAMES` | Canonical four UI primitive names on sidecar |
| Guard test | Asserts product catalog ∩ UI names = ∅ |

## Q&A

- Q: Why add a test if production already behaves correctly?
  A: Acceptance is the guard itself — prevents future regressions without
  relying on doc tokens alone.

- Q: Must this duplicate PYPOST-952's sidecar test?
  A: No requirement to remove sibling test; canonical home for product MCP
  catalog asserts is `test_mcp_server_impl.py`.

- Q: Does this ship UI tools on product MCP?
  A: No. Test-only; forbidden by parent PYPOST-918 acceptance.
