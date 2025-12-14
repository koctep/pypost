# PYPOST-26: Technical Debt Analysis

## Shortcuts Taken

- **Manual Route Handling**: The `MetricsManager` manually checks `environ['PATH_INFO'] == '/metrics'` inside a wrapper function. This is a simple WSGI approach but lacks the robustness of a full routing framework. However, for a single endpoint, it is sufficient.
- **Global Singleton Usage**: The `MetricsManager` is accessed via `MetricsManager()` singleton pattern throughout the codebase (`RequestWidget`, `HTTPClient`, `MCPServerImpl`). This creates a hidden dependency on global state, which can make testing harder in the future.

## Code Quality Issues

- **Coupling**: `HTTPClient` and `MCPServerImpl` now have a direct dependency on `pypost.core.metrics`. If metrics collection needs to be optional or swappable, this tight coupling will need refactoring (e.g., using dependency injection or an event bus).

## Missing Tests

- **Integration Tests**: There are no automated tests to verify that the HTTP server actually starts and serves metrics on the configured port.
- **Metric Verification**: No tests verify that specific actions (like clicking "Send") correctly increment the counters. Testing this would require inspecting the Prometheus registry state.

## Performance Concerns

- **Locking**: The `MetricsManager` uses locks for thread safety during server start/stop. This is low risk as these operations are infrequent (app start/settings change).
- **Synchronous Tracking**: Metric increments are synchronous method calls. `prometheus_client` operations are fast (atomic increments), so impact on request latency should be negligible.

## Follow-up Tasks

- [ ] Add unit tests for `MetricsManager` to verify singleton behavior and metric registration.
- [ ] Add integration tests to check if `/metrics` endpoint returns 200 OK and expected content type.
- [ ] Consider refactoring metric tracking into an event-based system to decouple core logic from monitoring infrastructure.
