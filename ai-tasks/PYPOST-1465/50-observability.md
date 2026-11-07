# PYPOST-1465: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: N/A — isolated MCP server collection refresh and worker IPC failures are contained
  within the affected server instance and never compromise host application stability.
- **ALERT**: N/A — per-server refresh or child worker failures do not disrupt peer collection or
  proxy servers.
- **CRIT**: N/A — unavailable workers or missing collection references transition only the affected
  server to the recoverable `failed` status.
- **ERR**:
  - `pypost/core/mcp_server_registry.py` (`refresh_collection`):
    `mcp_registry_refresh_collection_worker_failed instance_id=%s port=%d error=%s` and
    `mcp_registry_refresh_collection_variables_failed instance_id=%s port=%d error=%s` — records
    process-mode collection refresh failure when a worker has exited or IPC dispatch fails, logging
    only the sanitized error category or exception class name.
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`):
    `mcp_worker_ipc_error instance_id=%s pid=%s message=%s` — records sanitized worker-reported IPC
    errors without raw payloads.
  - `pypost/core/mcp_worker_process.py` (`worker_main`):
    `mcp_worker_update_tools_failed error=%s` — logs only the exception class name when decoding or
    registering tools in the worker fails, omitting tool definitions and variable values.
- **WARNING**:
  - `pypost/core/mcp_process_supervisor.py` (`update_tools`):
    `mcp_worker_update_tools_send_failed instance_id=%s` — warns when sending `UPDATE_TOOLS` over
    the parent control pipe fails due to a broken pipe or serialization error.
- **NOTICE**: N/A — operational collection refresh events use `INFO` under Python's standard
  `logging` hierarchy.
- **INFO**:
  - `pypost/core/mcp_server_registry.py` (`refresh_collection`):
    `mcp_registry_collection_refreshed instance_id=%s collection_id=%s execution_mode=%s tool_count=%d variable_count=%d hidden_key_count=%d`
    — records live collection tool and variable refresh across both `process` and `thread` execution
    modes with counts only, omitting request definitions and variable values.
  - `pypost/core/mcp_server_registry.py` (`_set_status`):
    `mcp_registry_status instance_id=%s state=%s message_present=%s` — records status transitions
    (such as `failed` when a refreshed worker is unavailable).
- **DEBUG**:
  - `pypost/core/mcp_process_supervisor.py` (`update_tools`, `_apply_ipc_message`):
    `mcp_worker_update_tools_sent instance_id=%s tool_count=%d` and
    `mcp_worker_ipc_ack instance_id=%s pid=%s correlating=%s` — traces `UPDATE_TOOLS` and
    `UPDATE_VARIABLES` IPC dispatch and worker acknowledgments without logging serialized tool
    schemas, request bodies, headers, or variable snapshots.

### Log Structure

Log format used:

- Structured logs: yes (`event_name key=value`)
- Includes context: yes (`instance_id`, `collection_id`, `execution_mode`, `pid`, `port`,
  `tool_count`, `variable_count`, `hidden_key_count`, `correlating`; never serialized `UPDATE_TOOLS`
  or `UPDATE_VARIABLES` payloads, request URLs/headers/bodies, or resolved secret values)
- Log levels: DEBUG, INFO, WARNING, ERROR (ERR)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: `MCPServerImpl._call_tool_inner` records tool call duration via
  `record_mcp_call_outcome` in `pypost/core/mcp_server_impl.py`.
- **Throughput**: `MCPServerImpl._call_tool_inner` records incoming requests and completed responses
  via `track_mcp_request_received` and `record_mcp_call_outcome` in `pypost/core/mcp_server_impl.py`.
- **Error rate**: tracked via `outcome="error"` in `record_mcp_call_outcome` and `failed` instance
  state counts in `MCPServerRegistry._publish_instance_metrics`.

### Business Metrics

Business metrics:

- `mcp_server_instances{state}`: updated by `MCPServerRegistry._publish_instance_metrics` via
  `set_mcp_server_instance_counts` whenever `refresh_collection` transitions an unavailable worker
  or missing-reference server to `failed` in `pypost/core/mcp_server_registry.py`.

### System Health Metrics

System health metrics:

- **Resource usage**: N/A — in-place `UPDATE_TOOLS` and `UPDATE_VARIABLES` IPC updates reuse the
  existing worker process and control pipe without spawning additional OS processes.
- **Component status**: `stopped`, `starting`, `running`, and `failed` states published per server
  instance through `MCPServerRegistry._publish_instance_metrics`.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (existing `mcp_server_instances` gauge and MCP tool execution metrics)
- [ ] Grafana dashboards (no new dashboard panels required)
- [ ] Alerting rules (existing failure state and error log patterns apply)
- [x] Log aggregation (structured `key=value` log events with strict secret and payload omission)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`mcp_worker_update_tools_sent`,
  `mcp_registry_collection_refreshed`, and `mcp_registry_unexpected_child_exit` /
  `mcp_registry_refresh_collection_worker_failed` verified via `caplog`)
- [x] Metrics are collected correctly (registry state transitions continue publishing instance
  counts via `_publish_instance_metrics`)
- [x] Logging works in error scenarios (exited worker during `refresh_collection` logs structured
  `ERROR` diagnostics and transitions only the dead instance to `failed`)
- [x] Large data structures are not logged (`UPDATE_TOOLS` request definitions, URLs, descriptions,
  and `UPDATE_VARIABLES` secret/variable values are absent from `caplog.text`)
- [x] Metrics are available for monitoring (registry status transitions publish instance counts)

## Notes

`tests/test_mcp_process_tool_refresh_repro.py` verifies via `caplog` that live collection tool and
variable refreshes emit structured supervisor (`mcp_worker_update_tools_sent`) and registry
(`mcp_registry_collection_refreshed`) events with counts only, while excluding request URLs, tool
descriptions, environment values, and secret collection variable values from captured logs.
