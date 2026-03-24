# PYPOST-23: Technical Debt Analysis


## Shortcuts Taken

- **Manual Route Handling**: The `MetricsManager` manually checks `environ['PATH_INFO'] == '/metrics'` inside a wrapper function. This is a simple WSGI approach but lacks the robustness of a full routing framework. However, for a single endpoint, it is sufficient. — [PYPOST-166](https://pypost.atlassian.net/browse/PYPOST-166)
- **Global Singleton Usage**: The `MetricsManager` is accessed via `MetricsManager()` singleton pattern throughout the codebase (`RequestWidget`, `HTTPClient`, `MCPServerImpl`). This creates a hidden dependency on global state, which can make testing harder in the future. — [PYPOST-167](https://pypost.atlassian.net/browse/PYPOST-167)

## Code Quality Issues

- **Coupling**: `HTTPClient` and `MCPServerImpl` now have a direct dependency on `pypost.core.metrics`. If metrics collection needs to be optional or swappable, this tight coupling will need refactoring (e.g., using dependency injection or an event bus). — [PYPOST-168](https://pypost.atlassian.net/browse/PYPOST-168)

## Missing Tests

- **Integration Tests**: There are no automated tests to verify that the HTTP server actually starts and serves metrics on the configured port. — [PYPOST-169](https://pypost.atlassian.net/browse/PYPOST-169)
- **Metric Verification**: No tests verify that specific actions (like clicking "Send") correctly increment the counters. Testing this would require inspecting the Prometheus registry state. — [PYPOST-170](https://pypost.atlassian.net/browse/PYPOST-170)

## Performance Concerns

- **Locking**: The `MetricsManager` uses locks for thread safety during server start/stop. This is low risk as these operations are infrequent (app start/settings change). — [PYPOST-171](https://pypost.atlassian.net/browse/PYPOST-171)
- **Synchronous Tracking**: Metric increments are synchronous method calls. `prometheus_client` operations are fast (atomic increments), so impact on request latency should be negligible. — [PYPOST-172](https://pypost.atlassian.net/browse/PYPOST-172)

## Follow-up Tasks

- Add unit tests for `MetricsManager` to verify singleton behavior and metric registration. — [PYPOST-173](https://pypost.atlassian.net/browse/PYPOST-173)
- Add integration tests to check if `/metrics` endpoint returns 200 OK and expected content type. — [PYPOST-174](https://pypost.atlassian.net/browse/PYPOST-174)
- Consider refactoring metric tracking into an event-based system to decouple core logic from monitoring infrastructure. — [PYPOST-175](https://pypost.atlassian.net/browse/PYPOST-175)
