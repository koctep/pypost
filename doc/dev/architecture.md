# Architecture Overview

PyPost follows a modular architecture, separating business logic (Core), data definitions (Models),
and the user interface (UI).

## Directory Structure

```text
pypost/
├── main.py                 # Application entry point
├── core/                   # Business logic
│   ├── http_client.py      # HTTP request handling (wrapping `requests`)
│   ├── template_engine.py  # Variable interpolation (Jinja2)
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

- **HTTPClient**: Handles the actual network communication. It executes requests asynchronously
  (typically using QThread or similar mechanisms) to keep the UI responsive.
- **TemplateEngine**: Processes strings like `{{base_url}}/api` using environment variables before
  sending requests.
- **Storage**: Manages saving and loading collections and environments to/from the filesystem (JSON
  format).

### User Interface (`pypost/ui/`)

Built with **PySide6** (Qt for Python).

- **MainWindow**: The central hub, managing the layout.
- **Widgets**: Specialized components like `RequestEditor` for composing requests and `ResponseView`
  for displaying results.
- **Dialogs**: Separate windows for specific tasks like editing environment variables
  (`env_dialog.py`).

## Data Flow

1. **Input**: User edits a request in the UI (URL, headers, body).
1. **Templating**: On sending, the `TemplateEngine` interpolates variables (e.g., replacing
   `{{token}}`).
1. **Execution**: The `HTTPClient` sends the request in a background thread.
1. **Response**: The result is captured, wrapped in a `Response` model, and sent back to the UI via
   signals.
1. **Display**: The `ResponseView` renders the response data (JSON highlighting, headers).
