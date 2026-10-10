# PYPOST-1353: Observability Implementation

## Logging Implementation

### Added Logs

UI state transitions, validation feedback, dialog lifecycle, and save operations in
`pypost/ui/dialogs/mcp_servers_dialog.py` and `pypost/ui/presenters/mcp_controls_presenter.py`
are mapped across syslog levels:

- **EMERG**: None (UI dialog interactions and validation rejections do not cause unrecoverable
  system failures).
- **ALERT**: None.
- **CRIT**: None.
- **ERR**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    `mcp_server_start_failed_ui message=%s` — logged when MCP server startup fails and an error
    dialog is displayed to the user (`message`).
- **WARNING**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    `mcp_servers_dialog_no_controller` — logged when the user requests opening the MCP servers
    dialog but no server controller is attached.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `Failed to add MCP server %s: %s` — logged when controller save raises `ValueError` during
    server creation (`server_id`, `error_message`).
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `Failed to update MCP server %s: %s` — logged when controller save raises `ValueError` during
    server update (`server_id`, `error_message`).
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor rejected save due to custom headers error: %s` — logged when saving a proxy
    server with malformed custom header definitions (`err_msg`).
- **NOTICE**: None.
- **INFO**:
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    `mcp_servers_dialog_opened server_count=%d` — logged when `_open_mcp_servers` opens the
    `McpServersDialog` with current configured server count and passes `builtin_view`.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `Adding new MCP server: id=%s, type=%s, name=%s (header_count=%d)` — logged on successful
    validation before invoking controller save for a new server.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `Updating MCP server: id=%s, type=%s, name=%s (header_count=%d)` — logged on successful
    validation before invoking controller save for an existing server.
  - `pypost/ui/presenters/mcp_controls_presenter.py`:
    `mcp_server_started host=%s port=%d` / `mcp_server_stopped` — logged on server state updates.
- **DEBUG**:
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor rejected save: collection and environment are required` — logged when
    `_accept_if_complete` rejects save due to missing environment or collection selection.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor rejected save: host is required` — logged when host field is blank.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor rejected save: upstream URL is required` — logged when upstream URL is
    missing for proxy servers.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor rejected invalid library variable draft` — logged when variable
    parsing fails.
  - `pypost/ui/dialogs/mcp_servers_dialog.py`:
    `MCP server editor accepted configuration for server id=%s` — logged when validation passes.

### Log Structure

Log format used:
- Structured logs: yes (consistent formatted events with key attributes: `id`, `type`, `name`,
  `server_count`, `header_count`, `message`).
- Includes context: yes (`server_id`, `server_count`, `type`, `header_count`).
- Log levels: DEBUG, INFO, WARNING, ERR.
- Sensitive data: no (no tokens, passwords, or header secret values are emitted in logs).

## UI Diagnostic State and Feedback Surfaces

In addition to syslog structured logging, the user interface provides comprehensive diagnostic
feedback across visual surfaces:

- **Dialog In-Place Validation Diagnostics**:
  - Validation message label (`self._error.setText(...)`):
    - When "Built-in" source is chosen and environment is empty, save is blocked and displays:
      `"Collection and environment are required."`
    - When host is empty: `"Host is required."`
    - When library collections are loading: `"Loading connected libraries…"`
    - When library collection is stale:
      `"The saved library collection is unavailable or stale. "
      "Select a valid collection before saving."`
    - When library profile is missing:
      `"The saved library profile is unavailable. Select a valid profile before saving."`
- **Error Popups and Notifications**:
  - `self._show_error(str(exc))` presents a modal warning box if the controller rejects a save
    (e.g., duplicate port, uncurated built-in collection path).
- **Tooltips and Read-Only Markers**:
  - Built-in collection dropdown items display `f"{entry.name} (read-only)"` with tooltip:
    `"Shipped with PyPost and updated on application upgrade (read-only)."`
  - Server overview table displays column 4 (Collection) as
    `f"Built-in / {display_name} (read-only)"` for all configurations with `bundled_library=True`.
- **Status Bar Presentation**:
  - `McpControlsPresenter._mcp_status_label`:
    - Multi-server summary: `"MCP Servers: {running} running; {failed} failed"` in green/red/gray.
    - Single server status: `"MCP: ON ({host}:{port})"`, `"MCP: OFF"`, or `"MCP: Starting..."`.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: Immediate in-memory validation and rendering of Built-in items with no network
  or disk overhead.
- **Throughput**: N/A (interactive desktop UI operations).
- **Error rate**: Tracked via failed server count in presenter status summary and controller
  metric publishing.

### Business Metrics

Business metrics:
- Monitored via downstream `MetricsTrackerProtocol`:
  - `track_mcp_library_save(category, duration)`
  - `set_mcp_server_instance_counts(counts)`

### System Health Metrics

System health metrics:
- **Resource usage**: Zero extraneous memory or disk allocations; built-in catalog is shared via
  in-memory `BuiltinCollectionView`.
- **Component status**: Monitored live via `McpServerController.mcp_server_status(server_id)`.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (Python `logging` module compatible with syslog, Loki, ELK, standard out)

## Validation Results

Validation results:
- [x] Logs are correctly formatted: Structured formatting across DEBUG, INFO, WARNING, ERR.
- [x] Metrics are collected correctly: Server counts and status summaries updated dynamically.
- [x] Logging works in error scenarios: Validation rejections and save failures logged properly.
- [x] Large data structures are not logged: Only IDs, names, types, and counts.
- [x] Metrics are available for monitoring: Presenter status labels and downstream metrics tracker.
- [x] Automated test verification: Test coverage in `tests/test_mcp_builtin_dialog.py` asserts:
  - Validation blocking and error label text (`"Collection and environment are required."`).
  - Read-only markers and tooltip messages on combo items.
  - Table overview read-only formatting (`"Built-in / <name> (read-only)"`).
  - Presenter `_open_mcp_servers` passing `builtin_view`.

## Notes

Built-in MCP server observability seamlessly integrates the UI presentation layer with the
underlying registry and controller observability layers established in PYPOST-1350, PYPOST-1351,
and PYPOST-1352.
