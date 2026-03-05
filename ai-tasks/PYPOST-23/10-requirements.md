# Requirements: PYPOST-23 - Adding Prometheus Metrics for Request Tracing

## Goals
Ensure observability of the request execution process in the application using Prometheus metrics. This will allow tracking the request lifecycle from clicking the button in the GUI to processing by the MCP server.

## User Stories
- As a developer/DevOps, I want to see Prometheus metrics to monitor request flow through the system.
- As a developer, I want to know the time between clicking the "Send" button and sending the request.
- As a developer, I want to know the request processing time by the MCP server.
- As a developer, I want to see counters of successful and failed requests at different stages.
- As a user, I want to be able to configure the IP address and port for metrics export via application settings.

## Functional Requirements

1.  **Prometheus Client Integration**:
    - Add `prometheus_client` library to dependencies.
    - Start an HTTP server to serve metrics (endpoint `/metrics`) on a separate port.

2.  **Settings**:
    - Add "Metrics Host" (IP) and "Metrics Port" fields to the settings dialog.
    - Default values: `0.0.0.0` (or `localhost`) for host and `9080` for port.
    - Metrics server must restart when settings change.

3.  **Metrics Collection (Trace)**:
    Implement the following metrics (Counter or Histogram/Summary):
    - **GUI Send Click**: Event of clicking the send button in the interface.
    - **Request Sent**: Event of sending an HTTP request by the client.
    - **Response Received**: Event of receiving a response by the client.
    - **MCP Request Received**: Event of receiving a request by the MCP server.
    - **MCP Response Sent**: Event of sending a response by the MCP server.

4.  **Labels**:
    - Desirable to add labels for method type (GET, POST, etc.) and status (success/error) where applicable.

## Non-functional Requirements
- **Performance**: Metrics collection should not significantly slow down the application.
- **Isolation**: Metrics server should not block the main UI thread (run in a separate thread).

## Constraints and Assumptions
- Application is written in Python (PyQt for GUI).
- `prometheus_client` library is used.
- Default port: 9080.
- Deploying an external Prometheus server (Docker, etc.) is **not required**.

## Main Entities
- **MetricsServer**: Component responsible for running the Prometheus HTTP server.
- **MetricsRegistry**: Centralized place for defining metrics.
- **Settings**: Extension of the settings model with new fields.

## Q&A
- **Q:** How to link GUI and MCP events?
    - **A:** If the MCP server runs in the same process, metrics will be shared. If different processes, metrics will be collected independently.
- **Q:** Do we need to restart the metrics server when changing the port?
    - **A:** Yes, it is necessary to implement "on-the-fly" restart of the metrics server when configuration settings change.
