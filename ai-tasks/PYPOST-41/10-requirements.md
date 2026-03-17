# PYPOST-41: Add Request Logging for History Viewing

## Summary

Implement HTTP request history logging in PyPost so users can review previously executed
requests, inspect their details, and reuse them without manually recreating the request.

## Background

PyPost is a desktop HTTP client built with PySide6. Requests are executed via
`RequestService.execute()`, which delegates to `HTTPClient` or `MCPClientService`. Currently
there is no record of past executions. Users lose all context once a tab is closed or a
new request is loaded.

## User Story

> As a PyPost user, I want to view a history of all requests I have sent, so that I can
> review past responses, reuse previous requests, and debug interactions without having to
> reconstruct them from scratch.

## Functional Requirements

### FR-1: History Recording
- Every successful invocation of `RequestService.execute()` must produce a history entry.
- Each entry must capture:
  - Timestamp (UTC, ISO-8601)
  - HTTP method (or `MCP`)
  - Resolved URL (after variable substitution)
  - Request headers (after substitution)
  - Request body (after substitution)
  - Response status code
  - Response time (ms)
  - Collection name and request name (if the request belongs to a saved collection;
    otherwise `null`)

### FR-2: History Persistence
- History entries must be persisted to disk so they survive application restarts.
- Storage location: `<user_data_dir>/pypost/history.json` (consistent with existing
  `StorageManager` convention using `platformdirs`).
- The history file must cap at a configurable maximum number of entries (default: 500).
  Oldest entries are removed when the cap is exceeded.

### FR-3: History UI Panel
- A **History** panel must be accessible from the main window (sidebar or dedicated tab).
- The panel must display a list of history entries showing:
  - Timestamp (local timezone, human-readable)
  - HTTP method badge (colour-coded to match existing method icons)
  - Resolved URL (truncated if too long)
  - Response status code
- The list must be ordered newest-first.
- The list must support **filtering** by URL substring (a text-input search field at the
  top of the panel).
- Selecting an entry must display its full details (method, URL, headers, body, status,
  response time) in a read-only detail view below or beside the list.

### FR-4: Reuse from History
- The history panel must provide a **"Load into Editor"** action (button or context menu)
  that loads the selected history entry's request data (method, URL, headers, body) into
  the currently active request editor tab.
- The loaded request must **not** be automatically saved to any collection; it is treated
  as an unsaved (scratch) request.

### FR-5: History Management
- Users must be able to **clear all history** via a button in the history panel (with a
  confirmation dialog).
- Individual entries must be deletable via a context-menu **"Delete"** action.

## Non-Functional Requirements

### NFR-1: Performance
- History recording must be asynchronous and must not add perceptible latency to request
  execution (write must not block the UI thread).

### NFR-2: Data Integrity
- If the history file is corrupt or unreadable, the application must start normally with
  an empty history and log a warning; it must not crash.

### NFR-3: Consistency
- The new `HistoryManager` must follow the same constructor-injection pattern as
  `StorageManager`, `ConfigManager`, and `MetricsManager`; no global singletons or
  module-level state.

### NFR-4: Testability
- `HistoryManager` and any history-related service logic must be unit-testable without
  a running Qt application.

## Data Model

```python
class HistoryEntry(BaseModel):
    id: str                          # UUID
    timestamp: str                   # UTC ISO-8601
    method: str                      # GET, POST, MCP, …
    url: str                         # resolved URL
    headers: Dict[str, str]          # resolved request headers
    body: str                        # resolved request body
    status_code: int                 # HTTP status code (0 = network error)
    response_time_ms: float          # round-trip time
    collection_name: Optional[str]   # None if ad-hoc
    request_name: Optional[str]      # None if ad-hoc
```

## Integration Points

| Component | Change |
|-----------|--------|
| `pypost/models/models.py` | Add `HistoryEntry` Pydantic model |
| `pypost/core/history_manager.py` | New: `HistoryManager` (load/save/append/clear) |
| `pypost/core/request_service.py` | Accept optional `HistoryManager`; record entry after each `execute()` call |
| `pypost/ui/widgets/history_panel.py` | New: Qt widget for history list + detail view |
| `pypost/ui/main_window.py` | Instantiate `HistoryManager`; add history panel to layout |
| `pypost/ui/presenters/tabs_presenter.py` | Emit signal or call callback when "Load into Editor" is triggered |

## Out of Scope

- Full response body persistence in history (storing large response bodies could exhaust
  disk space; only request data + status/timing is stored).
- Search/filter by method or status code (can be added in a future story).
- Syncing history across devices.
- Export of history to file.
