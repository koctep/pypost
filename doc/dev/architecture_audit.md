# Architecture and Package Boundary Audit

This document summarizes the PyPost architecture and package boundary audit (PYPOST-684).
The audit verifies layer separation, dependency direction, and service ownership across
`main.py`, `core/`, `models/`, and `ui/`. It complements the SOLID audit in
[solid_audit.md](solid_audit.md) (PYPOST-40) with a boundary-focused lens.

## Audit Report

Full report:
[ai-tasks/PYPOST-684/30-audit-report.md](../../ai-tasks/PYPOST-684/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** 141 Python modules (`core/` 68, `ui/` 61, `models/` 6)

## Executive Summary

The layered modular monolith is **largely intact**:

- `models/` has no upward imports.
- `ui/` depends on `core/` and `models/` as intended.
- HTTP execution, templating, and MCP tool calls converge on `RequestService.execute()`.
- Presenter extraction (PYPOST-43) keeps most UI orchestration out of widgets.

**One area needs attention:**

1. **Partial composition root** — `main.py` wires `ConfigManager`, `MetricsManager`,
   `TemplateService`, and `AlertManager`, but `MainWindow` still constructs
   `StorageManager`, `RequestManager`, `MCPServerManager`, and
   `StyleManager`. `HistoryManager` is created in `main.py` (PYPOST-694).

Capability docs (`request_execution.md`, `mcp_integration.md`, `template_service.md`,
`collection_loading.md`) align well with observed call chains. The main documentation gap
was the stale directory tree in [architecture.md](architecture.md) (refreshed in Step 7).

## Layer Map

| Layer | Package | Primary role | Upward deps |
| --- | --- | --- | --- |
| Composition root | `main.py` | Wire shared services | `ui/`, `core/` |
| Presentation | `pypost/ui/` | PySide6 windows, presenters, widgets | `core/`, `models/` |
| Core | `pypost/core/` | Request lifecycle, HTTP, templating, storage, MCP, metrics | `models/` |
| Qt integration | `pypost/core/qt/` | Threads, signals, timers bridging async work to UI | `core/`, `models/` |
| Data | `pypost/models/` | Schemas only | stdlib / typing |
| Integration (MCP) | `core/mcp_*` | ASGI server, tool exposure | `core/` services, `models/` |
| Test fixtures | `pypost/fixtures/` | MCP/integration test helpers | Not imported by production |

**Intended dependency direction** (dependencies point inward):

```text
main.py  →  ui/, core/
ui/      →  core/, models/
core/    →  models/          (Qt-free business logic)
core/qt/ →  core/, models/   (PySide6 integration glue)
models/  →  (stdlib only)
```

## Key Findings

### Layer boundaries

| ID | Finding | Severity |
| --- | --- | --- |
| L-001 | Layer map matches intent; Qt glue isolated in `core/qt/` | PASS |
| L-002 | Presenter pattern holds for collections, tabs, and env/MCP wiring | PASS |
| L-003 | `request_sync.is_tab_dirty` ties core semantics to UI `RequestTab` | **Remediated** ([PYPOST-696](https://pypost.atlassian.net/browse/PYPOST-696)) |
| L-004 | `StyleManager` is a UI concern living in `core/` | **Remediated** ([PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)) |
| L-005 | `fixtures/` not imported by production code | PASS |
| L-006 | `utils/` package is empty and unused | **Remediated** ([PYPOST-699](https://pypost.atlassian.net/browse/PYPOST-699)) |

### Dependency direction

| ID | Finding | Severity |
| --- | --- | --- |
| D-001 | Runtime core → ui import in `style_manager.py` | **Remediated** ([PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)) |
| D-002 | `models/` layer clean (no core/ui imports) | PASS |
| D-003 | `TYPE_CHECKING` guards used appropriately | PASS |
| D-004 | PySide6 imports in core modules | **Remediated** ([PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693)) |
| D-005 | Import smoke test passes (no circular-import failures) | PASS |
| D-006 | Protocol seams present where documented | PASS |

### Service ownership

| Service | Documented owner | Audit result |
| --- | --- | --- |
| HTTP execution | `RequestWorker` → `RequestService` → `HTTPClient` | PASS |
| Templating | `TemplateService` (single Jinja2 `Environment`) | PASS (hover duplicate: MEDIUM) |
| History | `RequestService` → `HistoryManager` | PASS (composition root: PYPOST-694) |
| MCP tools | `MCPServerManager`, `MCPServerImpl` | PASS (env suppliers in `EnvPresenter`) |

## Follow-up Work

Eleven prioritized remediation items (2 P1, 5 P2, 4 P3) are listed in
[ai-tasks/PYPOST-684/60-tech-debt.md](../../ai-tasks/PYPOST-684/60-tech-debt.md). Jira tickets
are created by the sprint orchestrator. R-P2-005 (stale `architecture.md` tree) was resolved in
PYPOST-684 Step 7.

## Documentation Alignment

| Document | Alignment | Notes |
| --- | --- | --- |
| `architecture.md` | Refreshed (PYPOST-684) | Tree and MCP/encryption/metrics sections updated |
| `testability.md` | Mostly aligned | Omits several MainWindow-constructed services |
| `request_execution.md` | Aligned | Pipeline, history by entry point, cancellation match code |
| `mcp_integration.md` | Aligned | Threading, per-call `RequestService`, inbound history product choice |
| `template_service.md` | Aligned | Consumer matrix matches grep results |
| `collection_loading.md` | Aligned | Presenters use `RequestManager.get_collections()` |

## Related

- [Architecture Overview](architecture.md)
- [SOLID and Maintainability Audit](solid_audit.md)
- [Unit Testability Patterns](testability.md)
- [MCP Integration](mcp_integration.md)
- [Request Execution](request_execution.md)

## Related Audits

Sibling Code Audit summaries — hub:
[documentation_audit.md § Code Audit Hub](documentation_audit.md#code-audit-hub).

- [Security and Secrets Handling Audit (PYPOST-685)](security_audit.md)
- [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
- [Code Quality and Maintainability Audit (PYPOST-687)](maintainability_audit.md)
- [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
- [Performance and Scalability Audit (PYPOST-689)](performance_audit.md)
- [Documentation and ADR Alignment Audit (PYPOST-690)](documentation_audit.md)
- [Dependencies and Supply Chain Audit (PYPOST-691)](dependencies_audit.md)
