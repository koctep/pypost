# Architecture: PYPOST-26 - Adding Prometheus Metrics for Request Tracing

## Research
- **`prometheus_client` Library**: Standard library for exporting metrics in Python. Allows starting an HTTP server via `start_http_server`.
- **PyQt Integration**: Starting an HTTP server is a blocking operation. It must be run in a separate thread (`threading.Thread`).
- **Server Restart**: `prometheus_client.start_http_server` starts a server that is difficult to stop gracefully without socket access or using internal API. However, `make_wsgi_app` can be used and run via `wsgiref.simple_server` (or another WSGI server), which is easier to manage (start/stop).
    - *Alternative*: Use `threading` and just start a new server on a new port, but the old port might remain occupied if the server is not stopped correctly.
    - *Decision*: Use `wsgiref.simple_server.make_server` in a separate thread. This allows calling `shutdown()` and `server_close()`.
- **Metrics Collection Points**:
    - GUI: `ResponseView` or `MainWindow` (button click signal).
    - Request: `RequestService` or `HttpClient`.
    - MCP: `McpServerImpl` or `McpServer`.

## Implementation Plan

1.  **`metrics` Module**: Create a new module `pypost/core/metrics.py`.
    - Class `MetricsManager`: Singleton or global object.
    - Methods `start_server(host, port)`, `stop_server()`, `restart_server(host, port)`.
    - Define metrics (Counter, Summary/Histogram) in `__init__`.
    - Wrapper methods for incrementing metrics (e.g., `track_gui_send_click()`).

2.  **Settings**:
    - Update `pypost/models/settings.py`: add fields `metrics_host` (str, default '0.0.0.0') and `metrics_port` (int, default 9080).
    - Update `pypost/ui/dialogs/settings_dialog.py`: add input fields.
    - On settings save, call `MetricsManager.restart_server()`.

3.  **Instrumentation**:
    - In `pypost/ui/widgets/request_editor.py` (or where Send button is) -> call `track_gui_send_click()`.
    - In `pypost/core/request_service.py` or `http_client.py` -> `track_request_sent()`, `track_response_received()`.
    - In `pypost/core/mcp_server_impl.py` -> `track_mcp_request_received()`, `track_mcp_response_sent()`.

4.  **Initialization**:
    - In `pypost/main.py`, initialize `MetricsManager` at startup with parameters from settings.

## Architecture

### Components

### MetricsManager Implementation Details
Using `wsgiref` for a managed server.

## Q&A
- **Q:** How to ensure metrics thread safety?
    - **A:** `prometheus_client` is thread-safe by default.
