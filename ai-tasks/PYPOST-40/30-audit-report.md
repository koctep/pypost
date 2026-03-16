# PYPOST-40: SOLID and Maintainability Audit Report

## Executive Summary

The PyPost codebase has a clear separation between core, models, and UI layers. Several SOLID
violations and maintainability risks were identified, with the most significant being the
**MainWindow** (1040 LOC) acting as a "god object," and widespread use of **singletons/globals**
(MetricsManager, template_service) that hinder testability and dependency inversion.

**Top recommendations:**

1. **P1** — Decompose MainWindow into smaller presenters/controllers (CollectionsPresenter,
   TabsPresenter, EnvironmentPresenter) to restore SRP and reduce coupling.
2. **P1** — Replace MetricsManager singleton and template_service global with constructor
   injection to improve DIP and testability.
3. **P2** — Introduce abstractions for HTTPClient and RequestService so core logic can be
   tested without network/IO.
4. **P2** — Unify collection loading: MainWindow should use RequestManager for all collection
   operations instead of bypassing it with direct StorageManager calls.

---

## Module Inventory

| Module | LOC | Responsibility |
|--------|-----|----------------|
| **core/request_manager** | 201 | Request/collection lifecycle, CRUD, index |
| **core/state_manager** | 43 | UI state persistence (tabs, expanded nodes) |
| **core/request_service** | 95 | Request execution orchestration (HTTP + MCP) |
| **core/http_client** | 198 | HTTP requests, SSE probe, template rendering |
| **core/script_executor** | 100 | Post-request Python script execution |
| **core/template_service** | 36 | Jinja2 variable interpolation |
| **core/storage** | 80 | Collections/environments persistence (JSON) |
| **core/config_manager** | 40 | App settings load/save |
| **core/worker** | 57 | Background request execution (QThread) |
| **core/metrics** | 286 | Prometheus metrics + MCP server (singleton) |
| **core/mcp_server_impl** | 231 | MCP tool execution, schema generation |
| **core/style_manager** | 45 | Qt stylesheet application |
| **models/models** | 26 | RequestData, Collection, Environment |
| **models/response** | 20 | ResponseData |
| **models/settings** | 19 | AppSettings |
| **ui/main_window** | 1040 | Layout, menus, tabs, tree, dialogs, MCP, env, settings |
| **ui/request_editor** | 227 | Request composition widget |
| **ui/response_view** | 290 | Response display, search |
| **ui/widgets/mixins** | 85 | VariableHoverMixin |
| **ui/dialogs/** | ~400 | Save, Env, Settings, Hotkeys, About |

**Total scope:** ~4100 LOC (excluding `__init__`, styles, code_editor, json_highlighter).

---

## SOLID Assessment

### Single Responsibility Principle (SRP)

| Finding | Location | Severity |
|---------|----------|----------|
| **MainWindow has many responsibilities** | `ui/main_window.py` | High |
| Layout, menus, tabs, tree view, context menus, environment selector, MCP status, settings, shortcuts, collection CRUD orchestration, tab state, tree state. A single class changes for layout, UX, and business logic. | | |
| **MetricsManager combines metrics + server + MCP** | `core/metrics.py` | Medium |
| Defines Prometheus counters, runs uvicorn server, hosts MCP resources. Three distinct concerns. | | |
| **RequestManager is well-scoped** | `core/request_manager.py` | — |
| Single responsibility: request/collection lifecycle. | | |
| **StorageManager handles both collections and environments** | `core/storage.py` | Low |
| Two persistence domains; could split into CollectionStorage and EnvironmentStorage. | | |

### Open/Closed Principle (OCP)

| Finding | Location | Severity |
|---------|----------|----------|
| **item_type branching** | `request_manager.py:115-134`, `184-201` | Medium |
| `delete_collection_item` and `rename_collection_item` use `if item_type == "collection"` / `"request"`. Adding a new item type requires modifying these methods. | | |
| **Request method branching** | `request_service.py:70-75` | Medium |
| `if request.method == "MCP"` vs. else. Adding a new protocol (e.g. gRPC) requires modifying execute(). | | |
| **SSE detection by URL** | `http_client.py:139-141` | Low |
| `is_sse_endpoint = request_data.method == "GET" and "/sse" in url`. Heuristic; new transports need code change. | | |

### Liskov Substitution Principle (LSP)

| Finding | Location | Severity |
|---------|----------|----------|
| **No inheritance hierarchy** | — | — |
| Core classes are not subclassed. LSP violations not observed. | | |
| **ScriptContext** | `script_executor.py` | — |
| Duck-typed; no inheritance. | | |

### Interface Segregation Principle (ISP)

| Finding | Location | Severity |
|---------|----------|----------|
| **Models are data-only** | `models/models.py` | — |
| RequestData, Collection, Environment are Pydantic models with no behavior. ISP satisfied. | | |
| **ScriptContext** | `script_executor.py` | — |
| Exposes env, set, get, log. Focused interface for script authors. | | |

### Dependency Inversion Principle (DIP)

| Finding | Location | Severity |
|---------|----------|----------|
| **RequestService creates HTTPClient, MCPClientService** | `request_service.py:23-24` | High |
| `self.http_client = HTTPClient()` — no injection. Hard to test or swap implementations. | | |
| **RequestWorker creates RequestService** | `worker.py:18` | High |
| `self.service = RequestService()` — no injection. | | |
| **MCPServerImpl creates RequestService** | `mcp_server_impl.py:19` | High |
| Same pattern. | | |
| **template_service global** | `template_service.py:36`, used in http_client, request_service, mcp_server_impl | High |
| Module-level singleton. No injection; hard to mock. | | |
| **MetricsManager() singleton** | Used in main_window, request_editor, response_view, request_service, http_client, mcp_server_impl | High |
| Direct `MetricsManager()` calls throughout. No injection. | | |
| **MainWindow creates all dependencies** | `main_window.py:66-74` | Medium |
| StorageManager, ConfigManager, RequestManager, StateManager, StyleManager, MCPServerManager — all instantiated in `__init__`. | | |
| **RequestManager receives StorageManager** | `request_manager.py:12` | Good |
| Constructor injection. | | |
| **StateManager receives ConfigManager** | `state_manager.py:9` | Good |
| Constructor injection. | | |

---

## Maintainability Assessment

### Coupling

- **UI → Core**: MainWindow imports RequestManager, StateManager, StorageManager, ConfigManager,
  Worker, etc. Direct dependency; no abstraction layer.
- **Core → Globals**: HTTPClient, RequestService, MCPServerImpl use template_service and
  MetricsManager as globals. Tight coupling.
- **main.py**: Creates ConfigManager, MetricsManager, MainWindow. MainWindow creates its own
  Storage, Config, etc. No shared composition root or DI container.

### Cohesion

- **MainWindow**: Low cohesion — layout, event handling, business orchestration, and
  persistence calls mixed.
- **RequestManager, StateManager, Storage, ConfigManager**: High cohesion.
- **MetricsManager**: Low — metrics definition, HTTP server, MCP server in one class.

### Extensibility

- **New request method**: Requires changes in RequestService.execute() and possibly HTTPClient.
- **New collection item type**: Requires changes in RequestManager (delete/rename) and
  MainWindow (tree model, context menu).
- **New storage backend**: StorageManager is concrete; no interface. Would require
  refactoring to abstract persistence.

### Testability

- **RequestService**: Hard to unit test — creates HTTPClient, uses template_service and
  MetricsManager.
- **HTTPClient**: Uses template_service and MetricsManager; real network in integration.
- **MainWindow**: Requires Qt application; no injection of managers. Integration-only.
- **ScriptExecutor**: Relatively testable — static method, injectable context.

---

## Prioritized Recommendations

### P1 — Address in near-term refactoring

| ID | Recommendation | Impact | Effort |
|----|----------------|-------|--------|
| R1 | Decompose MainWindow into presenters (CollectionsPresenter, TabsPresenter, EnvPresenter, etc.). MainWindow becomes a thin composition. | High | High |
| R2 | Replace MetricsManager singleton with injectable service. Pass via constructor from main.py. | High | Medium |
| R3 | Replace template_service global with injectable TemplateService. Pass to HTTPClient, RequestService, MCPServerImpl. | High | Medium |

### P2 — Plan for next sprint or tech-debt backlog

| ID | Recommendation | Impact | Effort |
|----|----------------|-------|--------|
| R4 | Introduce HTTPClientInterface (protocol) and inject into RequestService. Enables mocking for tests. | Medium | Medium |
| R5 | Unify collection loading: MainWindow should call RequestManager.reload_collections() and use get_collections() instead of loading from Storage directly. | Medium | Low |
| R6 | Replace item_type branching in RequestManager with strategy or registry pattern for extensibility. | Medium | Medium |
| R7 | Split MetricsManager: separate MetricsRegistry (counters) from MetricsServer (uvicorn + MCP). | Medium | Medium |

### P3 — Nice-to-have; document for future

| ID | Recommendation | Impact | Effort |
|----|----------------|-------|--------|
| R8 | Abstract StorageManager behind StorageInterface for collections and environments. | Low | Medium |
| R9 | Add protocol for request execution (ExecuteRequestProtocol) to support MCP/gRPC via OCP. | Low | High |

---

## Appendix: Finding References

| ID | File | Lines | Description |
|----|------|-------|-------------|
| F1 | main_window.py | 61-1041 | MainWindow class, 1040 LOC |
| F2 | metrics.py | 12-286 | MetricsManager singleton, metrics + server + MCP |
| F3 | template_service.py | 36 | template_service global |
| F4 | request_service.py | 23-24 | HTTPClient(), MCPClientService() direct creation |
| F5 | worker.py | 18 | RequestService() direct creation |
| F6 | mcp_server_impl.py | 19 | RequestService() direct creation |
| F7 | request_manager.py | 115-134 | delete_collection_item item_type branching |
| F8 | request_manager.py | 184-201 | rename_collection_item item_type branching |
| F9 | request_service.py | 70-75 | request.method == "MCP" branching |
| F10 | main_window.py | 199, 229 | storage.load_collections(), load_environments() bypass RequestManager |
| F11 | storage.py | 36-80 | save_collection, save_environments in one class |
