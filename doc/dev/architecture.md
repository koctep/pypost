# Architecture Overview

PyPost follows a modular architecture, separating business logic (Core), data definitions (Models),
and the user interface (UI).

## Directory Structure

```text
pypost/
├── main.py                 # Application entry point
├── core/                   # Business logic
│   ├── request_manager.py  # Request & Collection lifecycle management
│   ├── state_manager.py    # UI State persistence
│   ├── request_service.py  # Unified request execution service
│   ├── http_client.py      # HTTP request handling (wrapping `requests`)
│   ├── script_executor.py  # Python script execution environment
│   ├── template_service.py # Variable interpolation (Jinja2) Service
│   ├── storage.py          # Persistence (JSON)
│   ├── config_manager.py   # Configuration management
│   └── worker.py           # Background task execution
├── models/                 # Data structures
│   ├── models.py           # Core data models
│   ├── response.py         # HTTP Response structure
│   └── settings.py         # Application settings
├── ui/                     # User Interface (PySide6)
│   ├── main_window.py      # Main application window
│   ├── dialogs/            # Modal dialogs (Settings, Save, Env)
│   ├── widgets/            # Reusable UI components
│   │   ├── mixins.py       # UI Mixins (e.g. VariableHoverMixin)
│   └── styles/             # Qt Stylesheets (.qss) and custom styles
└── utils/                  # Helper utilities
```

## Core Components

### Data Models (`pypost/models/`)

The application uses classes (often Pydantic models or dataclasses) to define strict schemas for:

- **Requests**: Method, URL, headers, body.
- **Responses**: Status code, time, headers, content.
- **Environments**: Sets of variables for interpolation.

### Business Logic (`pypost/core/`)

- **RequestManager**: Manages the CRUD operations for Requests and Collections. Encapsulates searching and saving logic, decoupling it from the UI.
- **StateManager**: Manages the persistence of UI state (e.g., open tabs, expanded tree nodes), abstracting the configuration structure.
- **RequestService**: The central entry point for executing requests. It coordinates the `HTTPClient`
  for network calls and `ScriptExecutor` for post-request scripts.
- **HTTPClient**: Handles the actual network communication using `requests`.
- **ScriptExecutor**: Runs user-defined Python scripts in a sandboxed environment to manipulate variables.
- **TemplateService**: A service that manages the Jinja2 Environment and processes strings like `{{base_url}}/api`.
- **MetricsManager**: A singleton service managing the observability server. It runs an isolated `uvicorn` server providing both Prometheus metrics (`/metrics`) and an MCP interface (`/sse`) for accessing metrics as resources.
- **Storage**: Manages saving and loading collections and environments to/from the filesystem (JSON
  format).

### User Interface (`pypost/ui/`)

Built with **PySide6** (Qt for Python).

- **MainWindow**: The central hub, managing the layout. Delegates logic to `RequestManager` and `StateManager`.
- **Widgets**: Specialized components like `RequestEditor` for composing requests and `ResponseView`
  for displaying results. `VariableAware` widgets use `VariableHoverMixin` for shared tooltip logic.
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
