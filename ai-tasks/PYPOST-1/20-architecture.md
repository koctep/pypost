# PyPost Project Architecture

## 1. Project Structure

The project will be organized on a modular principle, with a clear separation of logic (Core), data (Models), and interface (UI).

```text
pypost/
├── main.py                 # Application entry point
├── core/                   # Business logic
│   ├── __init__.py
│   ├── http_client.py      # Request sending logic (requests)
│   ├── template_engine.py  # Variable processing {{var}}
│   └── storage.py          # Save/load management (JSON)
├── models/                 # Data structures (Dataclasses/Pydantic)
│   ├── __init__.py
│   ├── request.py          # HTTP Request model
│   ├── response.py         # HTTP Response model
│   ├── collection.py       # Collection model
│   └── environment.py      # Environment model
├── ui/                     # Graphical Interface (PySide6)
│   ├── __init__.py
│   ├── main_window.py      # Main window
│   ├── resources.py        # Icons and styles
│   ├── widgets/            # Reusable components
│   │   ├── request_editor.py # Request editing widget (URL, method)
│   │   ├── headers_table.py  # Headers table
│   │   ├── params_table.py   # Query parameters table
│   │   └── response_view.py  # Response viewer
│   └── dialogs/            # Dialogs (create collection, env settings)
└── utils/                  # Helper functions
    └── __init__.py
```

## 2. Main System Components

### 2.1. Data Models (Models)
We use `dataclasses` (or `pydantic` for validation) to describe structures.

*   **RequestData**:
    *   `id`: str
    *   `name`: str
    *   `method`: str (GET, POST, etc.)
    *   `url`: str
    *   `headers`: Dict[str, str]
    *   `params`: Dict[str, str]
    *   `body`: str (JSON content)
    *   `body_type`: str (json, text)

*   **Environment**:
    *   `id`: str
    *   `name`: str
    *   `variables`: Dict[str, str]

### 2.2. Business Logic (Core)

*   **HTTPClient**:
    *   Wrapper around the `requests` library.
    *   Executes requests asynchronously (in `QThread` or via `QRunnable`) so as not to block the UI.
    *   Returns a `ResponseData` object (status, time, headers, body).

*   **TemplateEngine**:
    *   Responsible for variable interpolation.
    *   Accepts a string (e.g., `{{base_url}}/api`) and a dictionary of variables.
    *   Returns the processed string.
    *   Used before sending a request for URL, Headers, Body.

*   **StorageManager**:
    *   Responsible for persistence.
    *   `save_collection(collection)`: saves to JSON.
    *   `load_collections()`: loads from folder.
    *   `save_environment(env)` / `load_environments()`.

### 2.3. User Interface (UI)

*   **MainWindow**:
    *   **Left Sidebar**: Collection tree (`QTreeView` / `QListWidget`).
    *   **Top Bar**: Environment selection (`QComboBox`), window management.
    *   **Central Widget**: Request tabs (`QTabWidget`).
*   **RequestTab**:
    *   Contains `RequestEditor` (top part) and `ResponseView` (bottom part or splitter).

## 3. Data Storage Schemas (JSON)

### 3.1. Collection (`collections/my_api.json`)
```json
{
  "id": "uuid...",
  "name": "My API",
  "requests": [
    {
      "id": "uuid...",
      "name": "Get Users",
      "method": "GET",
      "url": "{{base_url}}/users",
      "headers": { "Authorization": "Bearer {{token}}" },
      "params": { "limit": "10" },
      "body": ""
    }
  ]
}
```

### 3.2. Environments (`environments.json`)
```json
[
  {
    "id": "uuid...",
    "name": "Production",
    "variables": {
      "base_url": "https://api.example.com",
      "token": "secret_key"
    }
  }
]
```

## 4. Request Execution Flow (Data Flow)

1.  User clicks "Send".
2.  UI collects data from input fields into a `RequestData` object.
3.  UI retrieves the currently active environment from `EnvironmentManager`.
4.  `TemplateEngine` is called to substitute variables in URL, Headers, Body.
5.  The prepared request is passed to `HTTPClient` (started in a background thread).
6.  `HTTPClient` executes the request via `requests`.
7.  The result is returned via Signal to the UI.
8.  `ResponseView` displays the status, headers, and response body.

## 5. Technical Decisions
- **Multithreading**: Using `QThread` for network requests is mandatory so the interface does not freeze.
- **Error Handling**: `try-except` blocks around network calls and JSON parsing.
- **Dependencies**:
    - `PySide6`
    - `requests`
    - `jinja2` (for convenient variable templating; solution: use `jinja2` for reliability).
