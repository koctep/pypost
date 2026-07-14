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

**Two areas need attention:**

1. **Qt bleed into core** — Eight `core/` modules import PySide6 (workers, MCP lifecycle,
   state, metrics, encryption/env async). Documented for MCP/UI bridging but it weakens the
   presentation/core boundary.
2. **Partial composition root** — `main.py` wires `ConfigManager`, `MetricsManager`,
   `TemplateService`, and `AlertManager`, but `MainWindow` still constructs
   `StorageManager`, `RequestManager`, `HistoryManager`, `MCPServerManager`, and
   `StyleManager`.

Capability docs (`request_execution.md`, `mcp_integration.md`, `template_service.md`,
`collection_loading.md`) align well with observed call chains. The main documentation gap
was the stale directory tree in [architecture.md](architecture.md) (refreshed in Step 7).

## Layer Map

| Layer | Package | Primary role | Upward deps |
| --- | --- | --- | --- |
| Composition root | `main.py` | Wire shared services | `ui/`, `core/` |
| Presentation | `pypost/ui/` | PySide6 windows, presenters, widgets | `core/`, `models/` |
| Core | `pypost/core/` | Request lifecycle, HTTP, templating, storage, MCP, metrics | `models/` |
| Data | `pypost/models/` | Schemas only | stdlib / typing |
| Integration (MCP) | `core/mcp_*` | ASGI server, tool exposure | `core/` services, `models/` |
| Test fixtures | `pypost/fixtures/` | MCP/integration test helpers | Not imported by production |

**Intended dependency direction** (dependencies point inward):

```text
main.py  →  ui/, core/
ui/      →  core/, models/
core/    →  models/          (not core → ui at runtime)
models/  →  (stdlib only)
```

## Key Findings

### Layer boundaries

| ID | Finding | Severity |
| --- | --- | --- |
| L-001 | Layer map matches intent; MCP/worker Qt glue in `core/` is a caveat | PASS |
| L-002 | Presenter pattern holds for collections, tabs, and env/MCP wiring | PASS |
| L-003 | `request_sync.is_tab_dirty` ties core semantics to UI `RequestTab` | MEDIUM |
| L-004 | `StyleManager` is a UI concern living in `core/` | **Remediated** ([PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)) |
| L-005 | `fixtures/` not imported by production code | PASS |
| L-006 | `utils/` package is empty and unused | LOW |

### Dependency direction

| ID | Finding | Severity |
| --- | --- | --- |
| D-001 | Runtime core → ui import in `style_manager.py` | **Remediated** ([PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)) |
| D-002 | `models/` layer clean (no core/ui imports) | PASS |
| D-003 | `TYPE_CHECKING` guards used appropriately | PASS |
| D-004 | PySide6 imports in eight `core/` modules | MEDIUM |
| D-005 | Import smoke test passes (no circular-import failures) | PASS |
| D-006 | Protocol seams present where documented | PASS |

### Service ownership

| Service | Documented owner | Audit result |
| --- | --- | --- |
| HTTP execution | `RequestWorker` → `RequestService` → `HTTPClient` | PASS |
| Templating | `TemplateService` (single Jinja2 `Environment`) | PASS (hover duplicate: MEDIUM) |
| History | `RequestService` → `HistoryManager` | PASS (not in composition root: MEDIUM) |
| MCP tools | `MCPServerManager`, `MCPServerImpl` | PASS (env suppliers in `EnvPresenter`) |

## Prioritized Recommendations

| Priority | ID | Finding | Jira |
| --- | --- | --- | --- |
| **P1** | R-P1-001 | `style_manager.py` core → ui import | **Done** ([PYPOST-692](https://pypost.atlassian.net/browse/PYPOST-692)) |
| **P1** | R-P1-002 | Qt throughout `core/` | [PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693) |
| **P2** | R-P2-001 | `HistoryManager` outside composition root | [PYPOST-694](https://pypost.atlassian.net/browse/PYPOST-694) |
| **P2** | R-P2-002 | Partial composition root in `MainWindow` | [PYPOST-695](https://pypost.atlassian.net/browse/PYPOST-695) |
| **P2** | R-P2-003 | `request_sync.is_tab_dirty` in core | [PYPOST-696](https://pypost.atlassian.net/browse/PYPOST-696) |
| **P2** | R-P2-004 | Dual `TemplateService` for hover | [PYPOST-697](https://pypost.atlassian.net/browse/PYPOST-697) |
| **P2** | R-P2-005 | Stale `architecture.md` tree | Resolved in PYPOST-684 Step 7 |
| **P2** | R-P2-006 | Worker always builds `RequestService` | [PYPOST-698](https://pypost.atlassian.net/browse/PYPOST-698) |
| **P3** | R-P3-001 | Empty `utils/` package | [PYPOST-699](https://pypost.atlassian.net/browse/PYPOST-699) |
| **P3** | R-P3-002 | `template_service.py` LOC cap exceeded | [PYPOST-700](https://pypost.atlassian.net/browse/PYPOST-700) |
| **P3** | R-P3-003 | MCP inbound skips history | [PYPOST-701](https://pypost.atlassian.net/browse/PYPOST-701) |
| **P3** | R-P3-004 | `main.py` duplicates `PyPostStyle` setup | [PYPOST-702](https://pypost.atlassian.net/browse/PYPOST-702) |

Full remediation directions: [60-tech-debt.md](../../ai-tasks/PYPOST-684/60-tech-debt.md)

## Documentation Alignment

| Document | Alignment | Notes |
| --- | --- | --- |
| `architecture.md` | Refreshed (PYPOST-684) | Tree and MCP/encryption/metrics sections updated |
| `testability.md` | Mostly aligned | Omits several MainWindow-constructed services |
| `request_execution.md` | Aligned | Pipeline, history, cancellation match code |
| `mcp_integration.md` | Aligned | Threading, per-call `RequestService` verified |
| `template_service.md` | Aligned | Consumer matrix matches grep results |
| `collection_loading.md` | Aligned | Presenters use `RequestManager.get_collections()` |

## Related

- [Architecture Overview](architecture.md)
- [SOLID and Maintainability Audit](solid_audit.md)
- [Unit Testability Patterns](testability.md)
- [MCP Integration](mcp_integration.md)
- [Request Execution](request_execution.md)
