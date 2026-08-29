# PYPOST-1107: Observability Implementation

## Overview

PYPOST-1107 refactors the controller wiring for MCP controls:
1. Removed the unused legacy delegating method `EnvPresenter.set_mcp_server_controller(...)` from `pypost/ui/presenters/env_presenter.py`.
2. Directly wired `self.mcp_controls.set_server_controller(self.mcp_controller)` in `MainWindow.__init__` (`pypost/ui/main_window.py`).
3. Preserved all structured logging, warning diagnostics, and telemetry metrics in `McpControlsPresenter`, `MainWindow`, and `McpServerSettingsController`.

## Logging Implementation

### Review of Existing & Relevant Logs

The delegating method `EnvPresenter.set_mcp_server_controller` did not emit logs on its own (it merely forwarded the argument to `self.mcp_controls.set_server_controller`). Direct invocation from `MainWindow` preserves all observability guarantees and diagnostics across the UI layer.

- **INFO**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    - `mcp_servers_dialog_opened server_count=%d` — Logs dialog opening and available server count when the multi-server manager is launched.
    - `mcp_active_env_changed prev_env_id=%s new_env_id=%s` — Logs environment switching events affecting MCP.
    - `mcp_server_started host=%s port=%d` — Emitted when single-server endpoint starts.
    - `mcp_server_stopped` — Emitted when single-server endpoint stops.
    - `mcp_tools_overview_opened tool_count=%d` — Emitted when tools overview dialog is launched.
    - `mcp_activity_dialog_opened entry_count=%d` — Emitted when MCP activity log viewer opens.
  - `pypost/ui/mcp_server_controller.py`:
    - `mcp_server_started instance_id=%s` — Emitted when server instance starts.
    - `mcp_server_stopped instance_id=%s` — Emitted when server instance stops.
    - `mcp_server_restarted instance_id=%s` — Emitted when server instance restarts.
- **WARNING**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    - `mcp_servers_dialog_no_controller` — Emitted if the MCP Servers dialog action is triggered before a controller is attached.
- **ERR / ERROR**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    - `mcp_server_start_failed_ui message=%s` — Emitted when an MCP server start failure occurs.
- **DEBUG**:
  - `pypost/ui/mcp_server_controller.py`:
    - `mcp_manager_source source=injected/new`
    - `mcp_registry_source source=injected/new`
    - `mcp_server_activity_unavailable instance_id=%s`

### Log Structure

- Structured logs: Yes (key=value formatting and standard log parameterization without string concatenation)
- Includes context: Yes (`instance_id`, `server_count`, `prev_env_id`, `new_env_id`, `host`, `port`, `message`)
- Log levels used: `INFO`, `WARNING`, `ERROR`, `DEBUG`
- High volume / sensitive data: No large data structures, environment secrets, or payload bodies are logged.

## Metrics Implementation

### Telemetry & Business Metrics

- `self._metrics.track_mcp_active_env_changed()`:
  - Location: `McpControlsPresenter.track_active_env_changed` (`pypost/ui/presenters/mcp_controls_presenter.py`)
  - Tracked via OpenTelemetry metric instrument protocol (`MetricsTrackerProtocol`).
  - Recorded when an active environment transition occurs.

### Performance & Health Metrics

- Component lifecycle status: Tracked via `MCPServerRegistry.list_statuses()` and aggregated in UI status label (`MCP Servers: X running; Y failed`).

## Monitoring Integration

- [x] OpenTelemetry metrics protocol integration (`MetricsTrackerProtocol`)
- [x] Structured syslog-compatible logging with standard Python `logging` module
- [x] Diagnostic logging for missing controller attachment (`mcp_servers_dialog_no_controller`)

## Validation Results

- [x] Logs are correctly formatted (standard `key=value` diagnostic tokens)
- [x] Metrics and telemetry invocations verified
- [x] Logging works in error/warning scenarios (`mcp_servers_dialog_no_controller`, `mcp_server_start_failed_ui`)
- [x] No large data structures, credentials, or sensitive headers are logged
- [x] Zero logging regressions introduced by direct controller wiring in `MainWindow`

## Notes

The refactor directly addresses coupling and simplifies the call graph without altering any runtime logging contracts or telemetry emission points.
