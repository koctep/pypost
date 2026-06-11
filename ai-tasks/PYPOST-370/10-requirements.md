# PYPOST-370: MCP Tools and Metrics Integration Tests (Scope Closure)

## Goals

Close the PYPOST-38 technical-debt item that flagged missing automated integration coverage
for MCP tools and metrics. Prior work (PYPOST-368, PYPOST-367, existing metrics unit tests)
already satisfies the intent; this ticket documents that closure rather than duplicating tests.

## User Stories

- **As a maintainer**, I want clarity on which automated tests cover MCP tool SSE round-trips
  versus metrics MCP resources so follow-up work is not duplicated.
- **As a developer**, I want `doc/dev/testing.md` to point at the correct modules for MCP tool
  integration and metrics assertions.

## Definition of Done

- [x] Verify MCP tool live SSE integration coverage exists (`tests/test_mcp_server_integration.py`,
  PYPOST-368).
- [x] Verify metrics MCP resource assertions exist (`tests/test_metrics_manager.py`,
  `TestMetricsManagerMcpResource`).
- [x] Document scope closure in task artifacts and `doc/dev/testing.md`.
- [x] Record remaining gaps (live metrics SSE round-trip, outbound HTTP stub) as follow-up debt.

## Task Description

Source: `ai-tasks/PYPOST-38/60-tech-debt.md` — "Consider adding automated integration tests
for MCP tools and metrics (out of scope)." PYPOST-368 delivered MCP tool integration tests;
metrics MCP resource tracking is covered at unit level. No additional integration module is
required for this debt line.

## Q&A

- **Is new integration test code required?**
  - No. MCP tools: PYPOST-368. Metrics counters on `read_resource`: unit tests in
    `test_metrics_manager.py`.
- **What remains out of scope?**
  - Live metrics server MCP SSE round-trip and real outbound HTTP stub servers — tracked as
    follow-up debt in `60-tech-debt.md`.
