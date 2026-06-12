# PYPOST-684: Architecture and Package Boundary Audit Report

**Task:** PYPOST-684 — Audit architecture and package boundaries
**Date:** 2026-06-12
**Scope:** `pypost/main.py`, `pypost/core/`, `pypost/models/`, `pypost/ui/`, `pypost/utils/`, `pypost/fixtures/` (fixtures noted only)
**Baseline:** `doc/dev/architecture.md`, `doc/dev/testability.md`, and related capability docs listed in `20-architecture.md`
**Methodology:** Static import scans (ripgrep), module inventory, import smoke test (`.venv/bin/python`), call-chain tracing for HTTP/templating/history/MCP, documentation diff against live tree. No code changes.

## Executive Summary

PyPost's layered modular monolith is **largely intact**: `models/` has no upward imports; `ui/` depends on `core/` and `models/` as intended; HTTP execution, templating, and MCP tool calls converge on `RequestService.execute()` with a documented per-call `RequestService` for inbound MCP. Presenter extraction (PYPOST-43) keeps most UI orchestration out of widgets.

**Three areas need attention:**

1. **Dependency-direction violations** — `pypost/core/style_manager.py` imports `pypost.ui.styles.custom_style.PyPostStyle` at runtime (core → ui). This is the only confirmed runtime layer inversion outside `TYPE_CHECKING` guards.
2. **Qt bleed into core** — Eight `core/` modules import PySide6 (`worker.py`, `mcp_server.py`, `state_manager.py`, `metrics.py`, encryption/env workers, `style_manager.py`). Documented for MCP/UI bridging but it weakens the presentation/core boundary and blocks headless reuse of several "business" modules.
3. **Partial composition root** — `main.py` wires `ConfigManager`, `MetricsManager`, `TemplateService`, and `AlertManager`, but `MainWindow` still constructs `StorageManager`, `RequestManager`, `HistoryManager`, `MCPServerManager`, and `StyleManager`. This matches much of `testability.md` but leaves history and persistence outside the documented injection table, increasing test-setup cost.

**Documentation drift** is material: `doc/dev/architecture.md` directory tree omits ~40 core modules (MCP stack, encryption, key_sources, history, metrics server, presenters subpackage, etc.). Capability docs (`request_execution.md`, `mcp_integration.md`, `template_service.md`) align well with observed call chains.

**Import smoke test:** All key entry modules import successfully via `.venv/bin/python` (no circular-import failures at startup subgraph).

| Package | Python modules |
| --- | ---: |
| `pypost/` (total) | 141 |
| `pypost/core/` | 68 |
| `pypost/ui/` | 61 |
| `pypost/models/` | 6 |

---

## Layer Boundary Findings

### L-001 — Presentation / core / integration map matches intent (PASS with caveats)

Observed layering:

| Layer | Package | Primary role | Upward deps |
| --- | --- | --- | --- |
| Composition root | `main.py` | Wire shared services | `ui/`, `core/` |
| Presentation | `pypost/ui/` | PySide6 windows, presenters, widgets | `core/`, `models/` |
| Core | `pypost/core/` | Request lifecycle, HTTP, templating, storage, MCP, metrics | `models/` |
| Data | `pypost/models/` | Schemas only | stdlib / typing |
| Integration (MCP) | `core/mcp_*` | ASGI server, tool exposure | `core/` services, `models/` |

**Caveat:** MCP lifecycle (`MCPServerManager`) and request workers (`RequestWorker`) live in `core/` but depend on Qt signals/threads — functionally integration + presentation glue, not pure business logic.

**Impact:** New contributors may place Qt-dependent code in `core/` following existing patterns, further blurring layers.

### L-002 — Presenter pattern holds collection and tab orchestration (PASS)

- `CollectionsPresenter`, `TabsPresenter`, `EnvPresenter` delegate persistence to `RequestManager` / `StateManager` / `StorageInterface`.
- Collection reads follow `collection_loading.md`: tree and MCP tool discovery use `RequestManager.get_collections()` (via injected callable in `EnvPresenter`), not direct `StorageManager.load_collections()` from presenters.
- `MainWindow` constructs `StorageManager` once and passes it to `RequestManager` and `EnvPresenter` — acceptable UI-layer wiring, though not at `main.py`.

**Impact:** Low change risk for collection features; env/MCP wiring is centralized in `EnvPresenter`.

### L-003 — `request_sync.py` placement blurs core vs presentation (MEDIUM)

`pypost/core/request_sync.py` implements tab dirty-checking helpers (`is_tab_dirty`) that accept a UI `RequestTab` type (imported under `TYPE_CHECKING` only). Runtime functions operate on `RequestData` models; the tab-aware helper ties core package semantics to a presenter type.

**Impact:** Refactoring `RequestTab` requires touching `core/`; alternative would be moving dirty-check helpers to `ui/` or a thin `ui/request_sync.py`.

### L-004 — `style_manager.py` is a UI concern in `core/` (HIGH)

`StyleManager` loads QSS from `ui/styles/`, manipulates `QPalette`/`QStyleFactory`, and imports `PyPostStyle` from `ui/`. It is invoked from `MainWindow.apply_settings`, not from `main.py`.

**Impact:** Core package depends on UI assets and widgets; violates documented inward dependency rule.

### L-005 — `fixtures/` not imported by production code (PASS)

No production imports of `pypost.fixtures` found. Test-only surface as intended.

### L-006 — `utils/` package unused (LOW)

`pypost/utils/__init__.py` is empty; no imports of `pypost.utils` anywhere in the repo.

**Impact:** Dead package entry in architecture docs; harmless but confusing.

---

## Dependency Direction Findings

### D-001 — Runtime core → ui import: `style_manager.py` (HIGH)

```text
pypost/core/style_manager.py:7
  from pypost.ui.styles.custom_style import PyPostStyle
```

Also duplicated in `main.py:12` for application startup styling.

**Impact:** Importing `style_manager` pulls in `ui/`; prevents treating `core/` as UI-free; risk of circular imports if `ui/` ever needed `style_manager` at module level (currently safe).

### D-002 — `models/` layer clean (PASS)

No imports of `pypost.core` or `pypost.ui` in `pypost/models/`.

### D-003 — `TYPE_CHECKING` guards used appropriately (PASS)

`request_sync.py`, `storage.py`, `storage_interface.py`, `collection_item_strategies.py`, `main_window_signals.py` use `TYPE_CHECKING` for UI or heavy types — no runtime cycles observed.

### D-004 — PySide6 imports in `core/` (MEDIUM)

| Module | Qt usage |
| --- | --- |
| `worker.py` | `QThread`, `Signal` |
| `mcp_server.py` | `QObject`, `Signal` |
| `state_manager.py` | `QObject`, `QTimer` |
| `metrics.py` | `QObject`, `Signal` |
| `environment_storage_worker.py` | `QThread`, `Signal` |
| `environment_storage_gateway.py` | `QObject`, `Signal`, `QApplication` |
| `encryption_migration_worker.py` | `QThread`, `Signal` |
| `style_manager.py` | `Qt`, `QPalette`, `QStyleFactory` + ui import |

Documented in `mcp_integration.md` (Qt/async bridge) and `environment_storage_async.md`. Not import-direction violations per se, but **core is not UI-framework-agnostic**.

**Impact:** Unit tests for workers/MCP manager require Qt event loop or heavy mocking; headless tooling cannot reuse these modules without PySide6.

### D-005 — Import smoke test (PASS)

`.venv/bin/python -c` imports succeeded for: `pypost.main`, `pypost.core.request_service`, `pypost.core.mcp_server_impl`, `pypost.ui.main_window`, `pypost.core.http_client`, `pypost.core.template_service`, `pypost.core.request_sync`, `pypost.core.style_manager`.

No circular-import failures detected in the production entry subgraph.

### D-006 — Protocol seams present where documented (PASS)

`ExecuteRequestProtocol`, `HTTPClientProtocol`, `StorageInterface`, `MetricsTrackerProtocol` exist and are used by `RequestWorker`, `RequestService`, and tests per `testability.md`.

---

## Service Boundary Findings

### HTTP Execution

**Documented owner:** `RequestWorker` → `RequestService` → `HTTPClient` (`request_execution.md`).

**Observed GUI path:**

```text
TabsPresenter → RequestWorker (QThread) → RequestService.execute()
  → HTTPClient.send_request() / _execute_http_with_retry()
  → signals → ResponseView
```

**Observed MCP inbound path:**

```text
MCPServerImpl.call_tool → run_in_threadpool → _execute_request_sync()
  → RequestService(metrics, template_service)  # new instance per call
  → execute() → HTTPClient (same rendering rules)
```

| Finding | Severity | Detail |
| --- | --- | --- |
| S-HTTP-001 Shared execution core | PASS | GUI and MCP inbound share `RequestService.execute()`; MCP creates isolated service per call (PYPOST-138). |
| S-HTTP-002 MCP client path separate | INFO | `RequestService._execute_mcp()` + `MCPClientService` handle outbound MCP-as-HTTP-method; distinct from inbound collection MCP server. |
| S-HTTP-003 Default self-instantiation | MEDIUM | `RequestWorker` always constructs `RequestService` internally; `HTTPClient`/`MCPClientService` default-constructed inside `RequestService` when not injected. Documented for tests; production injects `template_service` and `history_manager` from `TabsPresenter` chain only. |
| S-HTTP-004 URL render once | PASS | `HTTPClient.send_request()` renders URL once; `request_execution.md` matches code. MCP URL/body rendered in `_execute_mcp()` only. |

### Templating

**Documented owner:** `TemplateService` — single Jinja2 `Environment` (`template_service.md`).

| Finding | Severity | Detail |
| --- | --- | --- |
| S-TMPL-001 Single render API | PASS | All `render_string` call sites route through `TemplateService`; no parallel `jinja2.Environment()` for request rendering outside `template_service.py` / `function_registry.py`. |
| S-TMPL-002 `mcp_secrets_policy` AST | PASS | Uses `template_service.parse()` + `jinja2.meta.find_undeclared_variables` — parse centralized, meta analysis only. |
| S-TMPL-003 Hover second instance | MEDIUM | `ui/widgets/mixins.py` holds module-level `_hover_template_service = TemplateService()`, separate from composition-root instance. Documented in `testability.md`; metrics diverge unless `VariableHoverResolver.set_metrics()` called (wired from `MainWindow`). |
| S-TMPL-004 LOC cap exceeded | LOW | `template_service.py` at 204 LOC vs 200 cap (`audit_baseline_metrics.py`). |

### History

**Documented owner:** `RequestService._record_execution_history` → `HistoryManager` (`request_execution.md`, `sensitive_data_masking_policy.md`).

| Finding | Severity | Detail |
| --- | --- | --- |
| S-HIST-001 Write path centralized | PASS | Only `RequestService` appends via `HistoryManager.append()` after execution; masking via `SensitiveDataMaskingPolicy`. |
| S-HIST-002 UI panel is presentation | PASS | `HistoryPanel` reads/filters/displays; delete/clear delegate to `HistoryManager`; cURL copy uses `CurlGenerator` with injected template service at call site. |
| S-HIST-003 Not in composition root | MEDIUM | `HistoryManager()` constructed in `MainWindow.__init__`, not `main.py` or `testability.md` injection table. Passed to `TabsPresenter` → `RequestWorker` → `RequestService`. |
| S-HIST-004 MCP inbound skips history | LOW (documented) | `MCPServerImpl._create_request_service()` omits `history_manager`; `mcp_integration.md` states inbound MCP tools do not record history. Asymmetric entry-point behavior by design. |

### MCP Tools

**Documented owners:** `MCPServerManager` (lifecycle), `MCPServerImpl` (tools), `McpSecretsPolicy` (schema vs execution secrets).

| Finding | Severity | Detail |
| --- | --- | --- |
| S-MCP-001 Lifecycle vs impl split | PASS | Manager: thread + uvicorn + Qt signals; Impl: Starlette routes, tool list/call. Matches `mcp_integration.md`. |
| S-MCP-002 Env suppliers wired in UI | PASS | `EnvPresenter` registers `_env_snapshot.snapshot_variables` / `snapshot_hidden_keys` on `MCPServerManager` — UI owns supplier hooks, core executes. |
| S-MCP-003 Metrics MCP separate surface | PASS | `MetricsServer` exposes observability MCP resources (`metrics://all`); shares transport helpers (`mcp_legacy_sse`, `mcp_transport_routes`) but distinct server instance from collection MCP. |
| S-MCP-004 `mcp_client_service` boundary | PASS | Outbound MCP protocol client used only from `RequestService` for `method == "MCP"` requests; not mixed with inbound server impl. |
| S-MCP-005 Activity log ownership | PASS | `McpActivityLog` owned by `MCPServerManager`; UI reads via signals to `EnvPresenter` / dialogs. |

---

## Documentation Alignment

Compared observed structure against `doc/dev/` references from `20-architecture.md`.

| Document | Alignment | Gaps |
| --- | --- | --- |
| `architecture.md` | **Stale** | Directory tree lists ~15 core files; live `core/` has 68 modules. Missing: MCP stack, `history_manager`, `metrics_server`, encryption/key_sources, `request_sync`, presenters subpackage, `fixtures/`. Component descriptions for `RequestService` / `HTTPClient` still accurate at high level. |
| `testability.md` | **Mostly aligned** | Composition-root table matches `main.py` for listed services. Omits `HistoryManager`, `StorageManager`, `RequestManager`, `MCPServerManager` (all constructed in `MainWindow`). Hover `TemplateService` exception documented. |
| `request_execution.md` | **Aligned** | Pipeline, history helpers, cancellation, URL render-once behavior match code. |
| `mcp_integration.md` | **Aligned** | Threading, transport routes, per-call `RequestService`, env injection, no inbound history — all verified. |
| `template_service.md` | **Aligned** | Consumer matrix matches grep results; no duplicate render paths found. |
| `collection_loading.md` | **Aligned** | Presenters use `RequestManager.get_collections()`; no presenter bypass found. |
| `state_manager.md` | **Aligned** | `StateManager` debounces UI session state; settings dialog uses `ConfigManager` directly. |
| `ui_mixins.md` | **Aligned** | Hover resolver/metrics pattern matches `mixins.py`. |
| ADR index | **N/A** | No central ADR index referenced from `doc/dev/README.md`; not a code defect. |

---

## Prioritized Recommendations

### P1 — High (remediate before major boundary refactors)

| ID | Finding | Remediation direction |
| --- | --- | --- |
| R-P1-001 | D-001 / L-004: `style_manager.py` core → ui import | Move `StyleManager` and theme application to `pypost/ui/` (e.g. `ui/styles/style_manager.py`) or extract `PyPostStyle` to a neutral module both layers can import. Remove `ui/` import from `core/`. |
| R-P1-002 | D-004: Qt throughout `core/` | Document as accepted boundary compromise **or** split `core/qt/` / `core/integration/` subpackages with explicit "requires PySide6" boundary; keep HTTP/templating/history in Qt-free modules. |

### P2 — Medium (schedule as tech debt)

| ID | Finding | Remediation direction |
| --- | --- | --- |
| R-P2-001 | S-HIST-003: `HistoryManager` outside composition root | Construct in `main.py` and inject into `MainWindow` / `TabsPresenter`; extend `testability.md` table. |
| R-P2-002 | Partial composition root in `MainWindow` | Optionally elevate `StorageManager`, `RequestManager`, `MCPServerManager` wiring to `main.py` for parity with `TemplateService` / `ConfigManager`. |
| R-P2-003 | L-003: `request_sync.is_tab_dirty` in core | Relocate tab-aware helper to `ui/`; keep `RequestData` copy/compare helpers in core or `models/`. |
| R-P2-004 | S-TMPL-003: dual `TemplateService` for hover | Inject composition-root `TemplateService` into hover mixin via `MainWindow` setup instead of module singleton (or document explicit acceptance). |
| R-P2-005 | `architecture.md` stale tree | Refresh directory structure and MCP/encryption/metrics sections in Step 7 dev docs. |
| R-P2-006 | S-HTTP-003: worker always builds `RequestService` | Allow injecting `ExecuteRequestProtocol` factory or service into `RequestWorker` for narrower integration tests. |

### P3 — Low (track or accept)

| ID | Finding | Remediation direction |
| --- | --- | --- |
| R-P3-001 | L-006: empty `utils/` package | Remove from docs or add shared helpers when needed. |
| R-P3-002 | S-TMPL-004: `template_service.py` LOC cap | Split expression helpers if growth continues. |
| R-P3-003 | S-HIST-004: MCP inbound no history | Accept as documented product choice; revisit only if agents need audit trail parity with GUI. |
| R-P3-004 | `main.py` duplicates `PyPostStyle` setup | Consolidate with `StyleManager.apply_theme` once style code moves to ui. |

---

## Finding Count by Priority

| Priority | Count | IDs |
| --- | ---: | --- |
| **P1** | 2 | R-P1-001, R-P1-002 |
| **P2** | 6 | R-P2-001 … R-P2-006 |
| **P3** | 4 | R-P3-001 … R-P3-004 |

*(Layer/service PASS items documented above are not counted as remediation tickets.)*

---

## Out of Scope (Explicit)

Per `10-requirements.md`:

- Code refactors or fixes (this report only)
- Full PYPOST-40 SOLID re-audit (referenced where overlapping)
- Performance profiling, security penetration testing, UI/UX review
- CI/build tooling or dependency version changes
- Target future architecture definition (remediation tasks may define)
- Follow-up Jira issues (Step 6 — `60-tech-debt.md`)

---

## Traceability

- **Task:** PYPOST-684
- **Architecture plan:** `ai-tasks/PYPOST-684/20-architecture.md`
- **Prior audit:** `ai-tasks/PYPOST-40/30-audit-report.md` (SOLID; boundary items cross-referenced, not duplicated)
- **Metrics script:** `scripts/audit_baseline_metrics.py` (2026-06-11 baseline)
