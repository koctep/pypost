# PYPOST-24: Technical Debt Analysis


## Shortcuts Taken

- **Global Metrics Manager**: `MetricsManager` is accessed as a global singleton. Dependency injection would be cleaner for testing. — [PYPOST-176](https://pypost.atlassian.net/browse/PYPOST-176)

## Missing Tests

- No unit tests for MCP metrics collection. Verified manually via `/metrics` endpoint. — [PYPOST-177](https://pypost.atlassian.net/browse/PYPOST-177)

## Follow-up Tasks

- Add unit tests for `MetricsManager`. — [PYPOST-178](https://pypost.atlassian.net/browse/PYPOST-178)
