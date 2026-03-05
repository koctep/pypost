# Requirements: PYPOST-24 - MCP Metrics

## Goals
Extend the metrics system (PYPOST-14) to track the performance and usage of the MCP server.

## User Stories
- As a developer, I want to see how many requests the MCP server processes.
- As a developer, I want to measure the execution time of MCP tools.
- As a developer, I want to track errors in MCP tools.

## Acceptance Criteria
- [ ] **MCP Request Counter**: A counter metric tracking the number of requests to the MCP server.
- [ ] **MCP Request Duration**: A histogram metric tracking the duration of MCP request processing.
- [ ] **Labels**: Metrics include labels for the tool name and execution status (success/error).

## Task Description
Add specific metrics for MCP to `MetricsManager` and call them from `MCPServerImpl`.

### Technical Details
- **Component**: `MetricsManager`, `MCPServerImpl`.
- **Metrics**:
    - `mcp_requests_total`: Counter (labels: `tool`, `status`).
    - `mcp_request_duration_seconds`: Histogram (labels: `tool`).
