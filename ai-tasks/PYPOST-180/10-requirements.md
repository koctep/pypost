# PYPOST-180: Automated tests groundwork for MCP test collection

## Goals

The MCP test collection (`examples/collections/mcp.json`) and companion environment
(`config/test/environments.json`) support manual verification via MCP Inspector, Cursor, and
PyPost UI. Contributors need automated checks that these committed artifacts stay valid and
expose the expected MCP tools so regressions are caught in CI before manual testing.

This task adds **groundwork** only. Live MCP round-trip tests that execute collection requests
are tracked separately ([PYPOST-181](https://pypost.atlassian.net/browse/PYPOST-181)).

## User Stories

- As a **contributor**, I want CI to fail when the MCP test collection JSON is invalid or no
  longer exposes the expected tools.
- As a **test author** (PYPOST-181), I want shared loaders and constants so integration tests
  can reuse the same collection and environment without duplicating paths.
- As a **maintainer**, I want the groundwork documented so future changes to
  `config/test` or `examples/collections` update tests in one place.

## Definition of Done

- [x] Shared helper module loads collection and environment from committed repo paths.
- [x] Automated tests validate JSON parses into PyPost models.
- [x] Tests assert expected MCP tool names (`sse_probe_metrics`, `sse_probe_main`) and that
  **List Tools** is not exposed as an MCP tool.
- [x] Tests assert the MCP Test environment has `enable_mcp: true`.
- [x] Developer documentation describes the new test surface and focused run command.
- [x] Full test suite passes.

## Task Description

Follow-up from [PYPOST-25](https://pypost.atlassian.net/browse/PYPOST-25) tech debt: "No
automated tests that use this collection." Explore `config/test`, `examples/collections`, and
existing MCP integration tests (`tests/test_mcp_server_integration.py`,
`tests/test_mcp_user_docs.py`) to align with project conventions.

## Q&A

- **Q:** Does this task run live MCP or HTTP requests?
  **A:** No — groundwork validates committed artifacts and tool metadata. PYPOST-181 adds
  execution tests.
- **Q:** Why not merge with PYPOST-181?
  **A:** Groundwork can land independently and unblocks integration tests without coupling to
  live server harness complexity.
