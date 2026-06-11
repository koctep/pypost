# PYPOST-370: Technical Debt Analysis

## Shortcuts Taken

- Closed as duplicate scope: MCP tool integration (PYPOST-368) and metrics MCP counter
  assertions (`test_metrics_manager.py`) satisfy the PYPOST-38 debt intent without a new
  combined integration module.

## Code Quality Issues

- None introduced.

## Missing Tests

- Live metrics server MCP SSE resource round-trip (`metrics://all` via `sse_client` against
  `MetricsManager` uvicorn) — deferred; unit coverage exists on `read_resource`.
- Integration test with real outbound HTTP (local stub server) — deferred from PYPOST-368.

## Performance Concerns

- None.

## Follow-up Tasks

- Live metrics server MCP SSE integration test —
  [PYPOST-563](https://pypost.atlassian.net/browse/PYPOST-563)
- MCP tool integration test with local HTTP stub server —
  [PYPOST-564](https://pypost.atlassian.net/browse/PYPOST-564)
