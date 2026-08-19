# Observability: PYPOST-1084

## Overview

Audited observability impacts of the dependency injection refactoring in `McpServerSettingsController`.

## Log Events & Metrics

- No logging statements were added, removed, or modified.
- `_collection_by_id` performed no logging previously.
- All existing logs in `pypost/ui/mcp_server_controller.py` (`mcp_manager_source`, `mcp_registry_source`, `mcp_server_reconfigure_finished`, `mcp_servers_persist_requested`, `mcp_server_activity_unavailable`) remain unchanged in format, level, and arguments.
- Metrics tracking through `metrics: MetricsTrackerProtocol` is forwarded unmodified to `MCPServerRegistry` and `MCPServerManager`.
