# PYPOST-152: Configurable MCP transport routes

## Goals

Developers maintaining PyPost MCP servers should change HTTP transport paths in one place
instead of hunting string literals across server implementations.

## User Stories

- As a **maintainer**, I want MCP route paths defined centrally, so protocol or deployment
  path changes require a single edit.
- As a **developer**, I want main and metrics MCP servers to share the same route constants,
  so behavior stays consistent.

## Definition of Done

- [x] Streamable HTTP path (`/mcp`) and legacy SSE paths (`/sse`, `/messages`) defined in one
  module.
- [x] `MCPServerImpl` and `MetricsServer` use those constants for Starlette mounts and
  `SseServerTransport`.
- [x] Routing tests reference constants (not duplicated literals).
- [x] Developer docs describe the configuration module.
- [x] Automated tests pass.

## Scope

**In scope:** Central constants module; wire main MCP and metrics MCP servers; tests and docs.

**Out of scope:** User-facing settings UI for custom paths; changing default path values;
  metrics server flat vs nested SSE layout (pre-existing difference).

## Q&A

| Question | Answer |
| --- | --- |
| AppSettings fields? | Not required — protocol paths are constants, not user prefs. |
| Parent debt item? | PYPOST-20 hardcoded routes follow-up. |

## Worklog

role: execution, step: 1, step_name: Requirements, tokens_used: 1800
