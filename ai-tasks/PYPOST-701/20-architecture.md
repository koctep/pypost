# PYPOST-701: Architecture

## Current behavior

| Entry point | `RequestService` construction | History recorded |
| --- | --- | --- |
| GUI (`RequestWorker`) | Injected `history_manager` from composition root | Yes — `HistoryManager.append()` |
| Inbound MCP (`MCPServerImpl._create_request_service`) | Fresh instance; no `history_manager` | No — `_record_execution_history()` is a no-op |

HTTP execution, templating, and error handling are otherwise shared via `RequestService.execute()`.

## Remediation plan (documentation only)

1. Add a **History asymmetry (product choice)** subsection to `mcp_integration.md` under
   environment/GUI parity — cite `MCPServerImpl._create_request_service()` and revisit
   criteria.
2. Extend `request_execution.md` history section with an entry-point matrix and cross-link.
3. Mark R-P3-003 **Done** in `architecture_audit.md`; refresh documentation alignment notes.

No code changes.

## Verdict

Design accepted as-is; documentation closes the audit finding.
