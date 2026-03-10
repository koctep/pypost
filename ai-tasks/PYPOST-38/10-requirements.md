# PYPOST-38: Testing Rules via MCP and Prometheus

## Goals

- **AI tests via embedded MCP** — the AI assistant in Cursor tests the application by
  calling the built-in MCP server tools.
- **Verification via Prometheus** — use Prometheus metrics to verify application
  behavior after MCP calls.

## User Stories

- As a developer, I want the AI assistant to call MCP tools and verify responses so that
  I can validate changes without manual steps.
- As a developer, I want the AI to use Prometheus metrics for verification so that
  behavior is checked end-to-end.

## Definition of Done

- Rules documented in `.cursor/lsr/do-testing.md`.
- AI knows how and what to verify via MCP and metrics.
- No new code — rules and documentation only.

## Task Description

**Scope:** PyPost embedded MCP server (port 1080), MetricsManager (port 9080).

**Functional scope:**

- Document how to test via MCP (connect, call tools, verify responses).
- Document how to use Prometheus metrics for verification.
- Create rules for the AI assistant in `.cursor/lsr/`.

**Out of scope:** New MCP server, pytest runner via MCP, UI automation.

**Programming language:** Python (PyPost).

## Q&A

- **Q:** Who runs tests? **A:** AI assistant in Cursor.
- **Q:** What to check? **A:** Both MCP tool responses and Prometheus metrics.
- **Q:** Where are rules? **A:** `.cursor/lsr/do-testing.md`.
