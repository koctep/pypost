# PYPOST-27: Technical Debt Analysis

## Shortcuts Taken

- **Global Metrics Manager**: `MetricsManager` is accessed as a global singleton. Dependency injection would be cleaner for testing.

## Missing Tests

- No unit tests for MCP metrics collection. Verified manually via `/metrics` endpoint.

## Follow-up Tasks

- Add unit tests for `MetricsManager`.
