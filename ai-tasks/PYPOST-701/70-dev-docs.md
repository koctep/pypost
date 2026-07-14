# PYPOST-701: Developer Documentation

## Summary

Documented inbound MCP history asymmetry as an accepted product choice across three dev docs.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/mcp_integration.md` | New **History asymmetry (product choice)** subsection |
| `doc/dev/request_execution.md` | Entry-point history matrix; inbound MCP cross-link |
| `doc/dev/architecture_audit.md` | R-P3-003 marked **Done**; alignment notes refreshed |

## Key statement

`MCPServerImpl._create_request_service()` builds a per-call `RequestService` without
`history_manager`. GUI sends record masked history via the composition-root
`HistoryManager`; inbound MCP tool calls do not. Revisit only if external agents require
persistent audit-trail parity with GUI executions.
