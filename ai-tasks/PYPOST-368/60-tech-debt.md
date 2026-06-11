# PYPOST-368: Technical Debt Analysis

## Shortcuts Taken

- `RequestService.execute` is mocked in integration tests so outbound HTTP stays deterministic.
  The exercised surface is MCP SSE transport, not full HTTP client execution.

## Code Quality Issues

- `MCPClientService.run` uses `asyncio.run` around `sse_client`, which relies on anyio task
  groups; live round-trips hang after `initialize` when called via `asyncio.run`. Integration
  tests use `anyio.run` + `ClientSession` directly instead.

## Missing Tests

- Integration test with real outbound HTTP (e.g. local stub server) — [PYPOST-370](https://pypost.atlassian.net/browse/PYPOST-370)
- Metrics server MCP resource round-trip — out of scope for PYPOST-38 debt chain.

## Performance Concerns

- None. Tests bind ephemeral ports and shut down uvicorn in fixtures; typical run &lt; 2s.

## Follow-up Tasks

- Fix `MCPClientService` to use `anyio.run` (or equivalent) so sync wrapper works against live
  SSE servers — [PYPOST-560](https://pypost.atlassian.net/browse/PYPOST-560)
