# PYPOST-41 Architecture: Add Request Logging for History Viewing

## 1. Overview

This document describes the design for HTTP request history logging in PyPost. The feature
records every executed request alongside its response metadata, persists entries to disk,
and exposes a History panel in the sidebar for browsing, filtering, and reloading requests.

The design follows the constructor-injection pattern already established by `MetricsManager`
and `TemplateService`, and mirrors the `StorageManager` approach for file persistence.

---

## 2. Affected Files

| File | Change |
|------|--------|
| `pypost/models/models.py` | Add `HistoryEntry` Pydantic model |
| `pypost/core/history_manager.py` | **New** – `HistoryManager` (load/save/append/delete/clear) |
| `pypost/core/request_service.py` | Accept `history_manager`; record entry after each `execute()` |
| `pypost/core/worker.py` | Accept `history_manager` + `collection_name`; pass to `RequestService` |
| `pypost/ui/widgets/history_panel.py` | **New** – Qt widget (list + detail view) |
| `pypost/ui/main_window.py` | Instantiate `HistoryManager`; wire `HistoryPanel` into sidebar |
| `pypost/ui/presenters/tabs_presenter.py` | Accept `history_manager`; resolve `collection_name`; expose `load_request_from_history()` |

---

## 3. Data Model

Add `HistoryEntry` to `pypost/models/models.py`:

```python
class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str                  # UTC ISO-8601, e.g. "2026-03-17T14:30:00.123456Z"
    method: str                     # "GET", "POST", "MCP", …
    url: str                        # resolved URL (after variable substitution)
    headers: Dict[str, str]         # resolved request headers
    body: str                       # resolved request body
    status_code: int                # HTTP status code; 0 = network error
    response_time_ms: float         # round-trip time in milliseconds
    collection_name: Optional[str] = None   # None for ad-hoc requests
    request_name: Optional[str] = None      # None for ad-hoc requests
```

---

## 4. `HistoryManager` (`pypost/core/history_manager.py`)

### Responsibility

- Load entries from `<user_data_dir>/pypost/history.json` on construction.
- Expose thread-safe `append()`, `delete_entry()`, `clear()`, and `get_entries()`.
- Persist state asynchronously (non-blocking write via `threading.Thread`) after each
  mutation.
- Enforce a configurable entry cap (default 500); drop oldest when exceeded.
- Survive corrupt/missing files gracefully (log warning, start empty).

### Interface

```python
class HistoryManager:
    DEFAULT_MAX_ENTRIES: int = 500

    def __init__(self, app_name: str = "pypost",
                 max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        """
        Resolves storage path from platformdirs, loads existing entries.
        Corrupt or missing file → empty list + warning log.
        """

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_entries(self) -> List[HistoryEntry]:
        """Return a copy of all entries ordered newest-first (immutable snapshot)."""

    # ── Write ─────────────────────────────────────────────────────────────────

    def append(self, entry: HistoryEntry) -> None:
        """
        Thread-safe. Insert entry at the front of the list.
        If len > max_entries, drop entries from the tail.
        Triggers an async save.
        """

    def delete_entry(self, entry_id: str) -> None:
        """Remove the entry with the given id. Triggers an async save."""

    def clear(self) -> None:
        """Remove all entries. Triggers an async save."""

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Read history.json; populate self._entries. Handles all I/O errors."""

    def _save_async(self) -> None:
        """Serialize self._entries to JSON in a daemon thread (non-blocking)."""
```

### Storage format

`history.json` stores a JSON array of serialised `HistoryEntry` objects (newest-first),
written with `indent=2` for human readability. This mirrors `StorageManager.save_environments()`.

### Thread-safety

All mutations are guarded by a `threading.Lock`. The background write thread acquires
the lock only to take a snapshot of `self._entries` at the start of the write, then
releases it before doing I/O, so reads/writes from the Qt main thread are never blocked
by disk I/O.

---

## 5. `RequestService` Changes (`pypost/core/request_service.py`)

### Constructor

```python
class RequestService:
    def __init__(
        self,
        metrics: MetricsManager | None = None,
        template_service: TemplateService | None = None,
        history_manager: HistoryManager | None = None,   # NEW
    ) -> None:
```

`history_manager` is optional and defaults to `None` (no recording). This preserves
backwards compatibility with all existing call sites and tests.

### `execute()` signature extension

```python
def execute(
    self,
    request: RequestData,
    variables: Dict[str, Any] = None,
    stream_callback: Callable[[str], None] = None,
    stop_flag: Callable[[], bool] = None,
    headers_callback: Callable[[int, Dict], None] = None,
    collection_name: str | None = None,   # NEW
    request_name: str | None = None,      # NEW
) -> ExecutionResult:
```

Both new parameters are optional and default to `None`. All existing callers continue to
work unchanged.

### History recording logic (appended after existing execute body)

```python
# After ExecutionResult is built:
if self._history_manager:
    resolved_url = self._template_service.render_string(request.url, variables)
    resolved_headers = {
        self._template_service.render_string(k, variables):
        self._template_service.render_string(v, variables)
        for k, v in request.headers.items()
    }
    resolved_body = self._template_service.render_string(request.body, variables)
    entry = HistoryEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        method=request.method,
        url=resolved_url,
        headers=resolved_headers,
        body=resolved_body,
        status_code=result.response.status_code,
        response_time_ms=result.response.elapsed_time * 1000.0,
        collection_name=collection_name,
        request_name=request_name,
    )
    self._history_manager.append(entry)
```

Template rendering here is idempotent and cheap (Jinja2 string ops). The duplicate render
(HTTPClient also renders internally) is an acceptable trade-off to keep `HistoryManager`
fully decoupled from transport details without requiring interface changes to `HTTPClient`.

**Error handling**: the entire history block is wrapped in a `try/except Exception`:
a failure to record history must never surface to the caller.

---

## 6. `RequestWorker` Changes (`pypost/core/worker.py`)

### Constructor additions

```python
class RequestWorker(QThread):
    def __init__(
        self,
        request_data: RequestData,
        variables: dict = None,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,   # NEW
        collection_name: str | None = None,               # NEW
    ) -> None:
        ...
        self._collection_name = collection_name
        self.service = RequestService(
            metrics=metrics,
            history_manager=history_manager,              # NEW
        )
```

### `run()` change

Pass `collection_name` and `request_name` to `service.execute()`:

```python
result = self.service.execute(
    self.request_data,
    self.variables,
    stream_callback=on_chunk,
    stop_flag=check_stop,
    headers_callback=on_headers,
    collection_name=self._collection_name,          # NEW
    request_name=self.request_data.name,            # NEW
)
```

---

## 7. `TabsPresenter` Changes (`pypost/ui/presenters/tabs_presenter.py`)

### Constructor addition

```python
class TabsPresenter(QObject):
    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,   # NEW
        parent: QObject | None = None,
    ) -> None:
        ...
        self._history_manager = history_manager
```

### `_handle_send_request()` change

Resolve `collection_name` before constructing the worker:

```python
collection_name = None
result = self._request_manager.find_request(request_data.id)
if result:
    _, found_collection = result
    collection_name = found_collection.name

worker = RequestWorker(
    request_data,
    variables=self._current_variables,
    metrics=self._metrics,
    history_manager=self._history_manager,   # NEW
    collection_name=collection_name,          # NEW
)
```

### New slot: `load_request_from_history()`

```python
def load_request_from_history(self, request_data: RequestData) -> None:
    """Opens a new scratch tab pre-populated with data from a history entry."""
    self.add_new_tab(request_data)
```

---

## 8. `HistoryPanel` Widget (`pypost/ui/widgets/history_panel.py`)

### Responsibility

A self-contained `QWidget` that reads from `HistoryManager` and allows browsing,
filtering, deleting entries, and loading them into the editor.

### Signals

```python
load_into_editor = Signal(RequestData)
```

### Layout

```
┌────────────────────────────────────┐
│  [Filter by URL…              ]    │  ← QLineEdit (search)
├────────────────────────────────────┤
│  LIST (QListWidget, newest-first)  │  ← filtered subset of entries
│   ┌──────────────────────────────┐ │
│   │ [GET]  2026-03-17 14:30  200 │ │
│   │ https://api.example.com/…    │ │
│   └──────────────────────────────┘ │
│   …                                │
├────────────────────────────────────┤
│  DETAIL (read-only form)           │  ← shown when entry selected
│   Method: GET                      │
│   URL:    https://…                │
│   Status: 200   Time: 142 ms       │
│   Headers: …                       │
│   Body:    …                       │
├────────────────────────────────────┤
│  [Load into Editor]  [Clear All]   │
└────────────────────────────────────┘
```

The list and detail pane are separated by a `QSplitter(Qt.Vertical)`.

### Key methods

```python
def __init__(self, history_manager: HistoryManager, parent=None) -> None: ...

def refresh(self) -> None:
    """Reloads entries from HistoryManager and re-applies filter."""

def _apply_filter(self, text: str) -> None:
    """Repopulates the list widget with entries whose URL contains `text`."""

def _on_selection_changed(self) -> None:
    """Populates the detail pane for the selected entry."""

def _on_load_into_editor(self) -> None:
    """Converts selected HistoryEntry to RequestData and emits load_into_editor."""

def _on_clear_history(self) -> None:
    """QMessageBox confirmation → history_manager.clear() → refresh()."""

def _on_context_menu(self, pos: QPoint) -> None:
    """Shows context menu with 'Delete' action for right-clicked entry."""
```

### RequestData reconstruction

When "Load into Editor" is triggered, the entry is converted to a fresh `RequestData`:

```python
request_data = RequestData(
    method=entry.method,
    url=entry.url,
    headers=entry.headers,
    body=entry.body,
)
```

`id` is freshly generated (default), ensuring it is treated as an unsaved scratch request.
`collection_name` / `request_name` are intentionally not set (per FR-4).

### Method colour coding

The method badge in list rows reuses the same icon dict (`self.icons`) already present in
`MainWindow`. `HistoryPanel` accepts an optional `icons: dict | None = None` parameter.
When icons are not provided the method is shown as a plain text label.

---

## 9. `MainWindow` Changes (`pypost/ui/main_window.py`)

### Instantiation

```python
self.history_manager = HistoryManager()   # NEW (after self.storage)
```

### Presenter injection

```python
self.tabs = TabsPresenter(
    self.request_manager, self.state_manager, self.settings,
    metrics=self.metrics,
    history_manager=self.history_manager,   # NEW
)
```

### Layout: sidebar tab widget

Replace:
```python
splitter.addWidget(self.collections.widget)
```

With:
```python
self.history_panel = HistoryPanel(self.history_manager, icons=self.icons)
sidebar = QTabWidget()
sidebar.addTab(self.collections.widget, "Collections")
sidebar.addTab(self.history_panel, "History")
splitter.addWidget(sidebar)
```

### Signal wiring

```python
self.history_panel.load_into_editor.connect(self.tabs.load_request_from_history)
```

History panel refresh is triggered from `TabsPresenter._on_request_finished()` by emitting
a new signal `request_executed = Signal()` on `TabsPresenter`, which `MainWindow` connects
to `self.history_panel.refresh`:

```python
self.tabs.request_executed.connect(self.history_panel.refresh)
```

This avoids tight coupling between worker internals and the UI panel.

---

## 10. Dependency Injection Flow (updated)

```
main.py
  ↓
ConfigManager → AppSettings
MetricsManager
  ↓
MainWindow(metrics)
  ├── StorageManager
  ├── HistoryManager()                      ← NEW
  ├── RequestManager(storage)
  ├── StateManager(config)
  ├── MCPServerManager(metrics)
  ├── CollectionsPresenter(request_mgr, state_mgr, metrics, icons)
  ├── TabsPresenter(request_mgr, state_mgr, settings, metrics, history_manager)
  │   └── (on send) RequestWorker(request_data, vars, metrics, history_manager, coll_name)
  │       └── RequestService(metrics, template_svc, history_manager)
  │           └── execute() → HistoryManager.append(entry)    ← NEW
  ├── EnvPresenter(storage, config, mcp_manager, settings, …)
  └── HistoryPanel(history_manager, icons)                    ← NEW
        ↑ refresh() ← tabs.request_executed signal
        ↓ load_into_editor → tabs.load_request_from_history()
```

---

## 11. Error Handling & Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| `history.json` is corrupt or unreadable | Warning logged; `_entries` starts as `[]`; app continues normally |
| Background write fails | Error logged; in-memory state unchanged; next write will retry |
| Entry cap exceeded | Entries beyond `max_entries` are removed from the tail (oldest-first) |
| Request execution fails (exception) | `RequestWorker.run()` catches and emits `error` signal; no history entry is recorded |
| History panel refresh while worker is running | `get_entries()` returns a snapshot copy under lock; UI is never blocked |

---

## 12. Test Strategy

All tests must be runnable without a Qt application (`QApplication` instance).
`HistoryManager` and the modified `RequestService` have no Qt dependencies.

### Unit: `tests/test_history_manager.py`

- `test_load_missing_file` – instantiate with nonexistent path; assert empty list.
- `test_load_corrupt_file` – write malformed JSON; assert empty list + no crash.
- `test_append_single_entry` – append one entry; `get_entries()` returns it.
- `test_append_enforces_cap` – append 501 entries with `max_entries=500`; assert len == 500
  and first entry is the most recent.
- `test_delete_entry` – append two entries; delete by id; assert only one remains.
- `test_clear` – append entries; clear; assert empty.
- `test_get_entries_newest_first` – append three entries with distinct timestamps; assert
  order is newest-first.
- `test_save_and_reload` – append entries; create a new `HistoryManager` pointing to the
  same file; assert entries are identical.
- `test_concurrent_appends` – append 50 entries from multiple threads; assert no data
  corruption and all 50 entries are present.

### Unit: `tests/test_request_service.py` (additions)

- `test_history_entry_recorded_after_execute` – inject `HistoryManager` mock; verify
  `append()` is called once with correct fields after a successful execute.
- `test_history_records_resolved_url` – use a template variable in URL; assert the stored
  URL is the rendered string.
- `test_history_not_recorded_on_exception` – have `http_client.send_request` raise; assert
  `append()` is never called.
- `test_no_history_manager_no_error` – execute without injecting `HistoryManager`; assert
  no exception is raised.
- `test_collection_name_propagated` – pass `collection_name="MyCol"`; assert stored entry
  has `collection_name="MyCol"`.

---

## 13. Outstanding Decisions / Risks

| # | Topic | Decision |
|---|-------|----------|
| D1 | Response body persistence | **Out of scope** per requirements; only request data + status/timing stored. |
| D2 | Resolved URL includes query params | The template-rendered URL from `request.url` does **not** include serialised `params` dict; params remain separate. This is acceptable since full URL reconstruction is complex and the raw URL template is already useful. |
| D3 | `HistoryPanel.refresh()` call site | Connected to `TabsPresenter.request_executed` signal (new). This keeps panel refresh decoupled from worker internals. |
| D4 | `HistoryManager` thread safety | Uses `threading.Lock` (not `QMutex`) to remain Qt-independent per NFR-4. |
| D5 | Sidebar layout change | Collections and History share a `QTabWidget` in the left pane (300 px). This is the minimum-impact change to the existing splitter layout. |
