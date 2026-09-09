# Architecture Overview

PyPost follows a modular architecture, separating business logic (Core), data definitions (Models),
and the user interface (UI). Package boundaries and layer rules are audited in
[architecture_audit.md](architecture_audit.md) (PYPOST-684).

## Directory Structure

As of 2026-06-12 (141 Python modules). Grouped by subsystem; see the live tree under `pypost/`.

```text
pypost/
├── main.py                 # Application entry point (composition root)
├── daemon.py               # Headless daemon entry point (PYPOST-1046)
├── version.py
├── core/                   # Business logic (68 modules)
│   ├── request_manager.py  # Request & collection lifecycle
│   ├── request_service.py  # Unified request execution
│   ├── request_persisted_fields.py  # RequestData copy/compare for persisted fields
│   ├── http_client.py      # HTTP handling (wraps `requests`)
│   ├── http_client_protocol.py
│   ├── execute_request_protocol.py
│   ├── script_executor.py  # Post-request Python script sandbox
│   ├── template_service.py # Jinja2 variable interpolation orchestration
│   ├── template_service_render.py # Template render + observability helpers
│   ├── function_registry.py, function_expression_resolver.py
│   ├── template_expression_tokenizer.py, template_expression_types.py
│   ├── storage.py          # JSON persistence (collections, environments)
│   ├── storage_interface.py, collection_item_strategies.py
│   ├── config_manager.py   # Configuration management
│   ├── history_manager.py  # Execution history read/write
│   ├── sensitive_data_masking_policy.py, curl_generator.py
│   ├── environment_ops.py, environment_messages.py
│   ├── environment_variables_adapter.py, env_variable_snapshot.py
│   ├── environment_secrets_codec.py
│   ├── encryption_config.py, encryption_key.py
│   ├── encryption_migration.py
│   ├── key_provider.py, key_source_constants.py
│   ├── key_sources/        # Keyring, env, file, chain, factory, registry
│   ├── websocket_client.py # WebSocket transport seam (QWebSocketClientTransport)
│   ├── websocket_session.py # WebSocket connection session & state machine
│   ├── websocket_stream.py # Bounded ring buffer & drop accounting
│   ├── websocket_codecs.py # Message codecs (Text, JSON, Binary Hex/Base64)
│   ├── websocket_export.py # Transcript export (JSON, NDJSON, CSV)
│   ├── websocket_session_slots.py # Concurrency limit (SessionSlots)
│   ├── websocket_templating.py, websocket_tls.py
│   ├── mcp_websocket_probe.py # Bounded MCP WebSocket probe runner
│   ├── mcp_server_impl.py  # Starlette routes, tool list/call
│   ├── mcp_client_service.py   # Outbound MCP protocol client
│   ├── mcp_secrets_policy.py, mcp_activity_log.py, mcp_tool_contract.py
│   ├── mcp_tools_overview.py, mcp_transport_routes.py
│   ├── mcp_legacy_sse.py, mcp_streamable_http.py
│   ├── metrics_registry.py, metrics_server.py, metrics_otel.py
│   ├── metrics_protocol.py, alert_manager.py
│   ├── qt/                 # PySide6 integration (threads, signals, timers)
│   │   ├── worker.py           # Background request execution (QThread)
│   │   ├── mcp_server.py       # MCP lifecycle (thread + uvicorn + Qt signals)
│   │   ├── state_manager.py    # Debounced UI session state persistence
│   │   ├── metrics.py          # MetricsManager facade (Qt signals)
│   │   ├── collection_storage_worker.py, collection_storage_gateway.py
│   │   ├── environment_storage_worker.py, environment_storage_gateway.py
│   │   └── encryption_migration_worker.py
│   ├── bind_address_validation.py, server_bind.py
│   ├── variable_name_validation.py, hidden_toggle_log_policy.py
│   ├── yaml_json_converter.py, constants.py
│   └── ...
├── models/                 # Data structures (6 modules)
│   ├── models.py           # Core data models (requests, collections, environments)
│   ├── response.py         # HTTP response structure
│   ├── settings.py         # Application settings
│   ├── errors.py, retry.py
├── ui/                     # User Interface — PySide6 (65 modules)
│   ├── main_window.py      # Main application window
│   ├── main_window_signals.py
│   ├── mcp_server_controller.py  # MCP persistence/lifecycle (PYPOST-1071)
│   ├── presenters/         # CollectionsPresenter, TabsPresenter, EnvPresenter,
│   │                       # McpControlsPresenter, WebSocketPresenter
│   ├── dialogs/            # Settings, Save, Env, MCP activity, hotkeys, about
│   ├── widgets/            # RequestEditor, ResponseView, HistoryPanel, body editor,
│   │                       # WebSocketTab, WebSocketStreamView, WebSocketComposer
│   │   ├── mixins.py       # VariableHoverMixin and shared tooltip logic
│   │   ├── environments/   # Environment list and variables widgets
│   │   ├── fold/           # Body editor code folding
│   │   ├── settings/       # Settings dialog sections
│   │   └── validate/       # Body format validators (JSON, YAML, XML)
│   ├── delegates/          # Collection rename, environment name delegates
│   ├── styles/             # Qt stylesheets (.qss), StyleManager, custom styles
│   ├── theme/              # JSON syntax highlighting theme
│   ├── hotkeys.py, collection_item_dialogs.py
│   └── request_save_orchestrator.py
└── fixtures/               # Test fixtures only (not imported by production)
    └── mcp_test_fixtures.py
```

**Layer rules:** `models/` → stdlib only; `core/` → `models/` (Qt-free); `core/qt/` → PySide6
integration glue; `ui/` → `core/`, `core/qt/`, `models/`. Appearance orchestration
(`StyleManager`) lives in `ui/styles/` — see [ui_font_and_styles.md](ui_font_and_styles.md).
Qt-dependent integration modules live in `core/qt/` — see
[testability.md](testability.md#qt-integration-layer).

## Composition root (`main.py`)

`main.py` wires shared services before `MainWindow` is shown. `ConfigManager` is created first
because several startup components need `AppSettings` from disk before the UI exists:

```text
ConfigManager.load_config() → AppSettings
    ├─ MetricsManager.start_server(host, port)
    ├─ AlertManager(log_path, webhook, …)
    ├─ StorageManager.apply_encryption_settings(settings)
    ├─ RequestManager(storage, defer_initial_load=True)
    ├─ MCPServerManager(metrics, template_service)
    └─ MainWindow(…injected services…) → StateManager (same AppSettings object)
```

`ComposedApp` registers each acquired resource in an idempotent LIFO lifecycle owner. Partial
composition, normal desktop exit, agent shutdown, and attach-host startup failure therefore share
one rollback contract. See [application resource lifecycle](application_lifecycle.md).

The same `ConfigManager` instance is injected into `MainWindow` so `settings.json` is read once
(PYPOST-404). Do not lazy-create `ConfigManager` inside `MainWindow` in production. See
[testability.md](testability.md#composition-root) and
[PYPOST-404 dev notes](../../ai-tasks/PYPOST-404/70-dev-docs.md).

`MainWindow` still constructs `StyleManager` and presenters/widgets internally.
`StorageManager`, `RequestManager`, and `MCPServerManager` are created in `main.py` and injected
(PYPOST-695). `HistoryManager` is created in `main.py` and injected (PYPOST-694). Remaining
partial composition root items are tracked in
[architecture_audit.md](architecture_audit.md#executive-summary) (PYPOST-684).

### Headless daemon composition root (`daemon.py`)

Headless execution (`pypost/daemon.py`, `pypost-daemon`) runs without desktop widgets, creating a
`QCoreApplication` and `DaemonRuntime` with strict path resolution and snapshot loading. See
[daemon.md](daemon.md) (PYPOST-1046) for architecture and lifecycle details.

## Core Components

### Data Models (`pypost/models/`)

The application uses classes (often Pydantic models or dataclasses) to define strict schemas for:

- **Requests**: Method, URL, headers, body.
- **Responses**: Status code, time, headers, content.
- **Environments**: Sets of variables for interpolation.

### Business Logic (`pypost/core/`)

- **RequestManager**: Manages the CRUD operations for Requests and Collections. Encapsulates searching and saving logic, decoupling it from the UI. Maintains an internal index for O(1) request lookup. UI code reads collections via `get_collections()` only; see [collection_loading.md](collection_loading.md).
- **StateManager**: Manages debounced persistence of UI session state (`expanded_collections`,
  `open_tabs`, `last_environment_id`) on a shared `AppSettings` instance loaded by
  `ConfigManager`. UI mutations debounce disk writes (300 ms); pending state is flushed on
  application exit via `flush_pending_save()`. Settings dialog saves bypass `StateManager` and
  write immediately through `ConfigManager`. See [state_manager.md](state_manager.md).
- **RequestService**: The central entry point for executing requests. It coordinates the `HTTPClient`
  for network calls and `ScriptExecutor` for post-request scripts.
- **HTTPClient**: Handles the actual network communication using `requests`. Responsible for rendering templates and preparing request parameters.
- **ScriptExecutor**: Runs user-defined Python scripts in a sandboxed environment to manipulate variables.
- **TemplateService**: Central Jinja2 service for all runtime `{{...}}` substitution (replaced
  the removed `TemplateEngine` in PYPOST-18). See [template_service.md](template_service.md).
- **MetricsManager**: Composition-root facade (constructed in `main.py`) composing
  `MetricsRegistry` (Prometheus counters) and `MetricsServer` (observability HTTP/MCP). Runs an
  isolated `uvicorn` server providing Prometheus metrics (`/metrics`) and Streamable HTTP MCP
  (`/mcp`) for accessing metrics as resources. See
  [mcp_integration.md](mcp_integration.md).
- **Storage**: Manages saving and loading collections and environments to/from the filesystem (JSON
  format). When environment encryption is enabled, `EnvironmentStorageGateway` delegates encrypted
  load/save to `EnvironmentStorageWorker` on a background thread (see
  [environment_storage_async.md](environment_storage_async.md)).
- **HistoryManager**: Persists execution history entries written by `RequestService` after each
  request. Masking uses `SensitiveDataMaskingPolicy`. The UI `HistoryPanel` reads and filters;
  see [request_execution.md](request_execution.md) and
  [sensitive_data_masking_policy.md](sensitive_data_masking_policy.md).
- **MCP stack**: `MCPServerManager` owns lifecycle (thread, uvicorn, Qt signals);
  `MCPServerImpl` exposes Starlette routes and tool list/call. Inbound MCP tools execute via
  per-call `RequestService` instances; outbound MCP-as-HTTP uses `MCPClientService` from
  `RequestService._execute_mcp()`. See [mcp_integration.md](mcp_integration.md) and
  [mcp_secrets_policy.md](mcp_secrets_policy.md).
- **Encryption**: `key_sources/` resolves encryption keys (keyring, env, file, chain);
  `encryption_migration_worker.py` migrates encrypted environments on a background thread.
  See [environment_encryption_at_rest.md](environment_encryption_at_rest.md).
- **WebSocket Subsystem**: Manages WebSocket connection sessions, lifecycle state transitions,
  bounded ring buffer streaming, frame codecs (Text, JSON, Binary), sequence execution, sensitive
  secret masking, and bounded MCP probe tools. See [websocket_architecture.md](websocket_architecture.md).

### User Interface (`pypost/ui/`)

Built with **PySide6** (Qt for Python).

- **MainWindow**: The central hub, managing the layout. Delegates orchestration to presenters
  (`CollectionsPresenter`, `TabsPresenter`, `EnvPresenter`) introduced in PYPOST-43, and MCP
  persistence/lifecycle to `McpServerSettingsController` (PYPOST-1071).
- **Presenters**: Keep collection, tab, and environment wiring out of widgets. MCP status,
  buttons and dialogs live in `McpControlsPresenter`, whose widgets `EnvPresenter` hosts in
  the environment bar (PYPOST-1071, PYPOST-1082). See [presenter_architecture.md](presenter_architecture.md).
  Collection reads go through `RequestManager.get_collections()` only — see
  [collection_loading.md](collection_loading.md).
- **Widgets**: Specialized components like `RequestEditor` for composing requests and `ResponseView`
  for displaying results. `ResponseView` includes a status bar, search bar (plain-text search with
  Previous/Next, match case, counter), and read-only body. `VariableAware` widgets use
  `VariableHoverMixin` for shared tooltip logic (generic `QWidget` mixin; see
  [ui_mixins.md](ui_mixins.md)).
- **Dialogs**: Separate windows for specific tasks like editing environment variables
  (`env_dialog.py`).

## Data Flow

1. **Input**: User edits a request in the UI (URL, headers, body).
1. **Execution**: The `RequestWorker` calls `RequestService.execute()` in a background thread.
1. **Service Logic**:
   - `RequestService` calls `HTTPClient` to perform the network request.
   - If successful, it calls `ScriptExecutor` to run any post-request scripts.
1. **Response**: The `ExecutionResult` (containing response, logs, and updated variables) is returned.
1. **UI Update**: The worker emits signals with the result, and `ResponseView` renders the data.
