# PYPOST-41 Developer Documentation: Request History

## Overview

PYPOST-41 adds persistent HTTP request history to PyPost. Every successful request execution
produces a `HistoryEntry` that is saved to disk and displayed in a new **History** sidebar tab.
Users can filter entries by URL, inspect full request/response metadata, delete individual
entries, clear all history, and reload any entry into the request editor.

---

## Architecture at a Glance

```
MainWindow
  ├── HistoryManager()                    ← persists entries to <user_data>/pypost/history.json
  ├── TabsPresenter(history_manager=...)
  │   └── (on send) RequestWorker(history_manager=..., collection_name=...)
  │       └── RequestService(history_manager=...)
  │           └── execute() → HistoryManager.append(entry)
  └── HistoryPanel(history_manager=...)
        ↑ refresh()  ← tabs.request_executed Signal
        ↓ load_into_editor Signal → tabs.load_request_from_history()
```

---

## Key Components

### `HistoryEntry` — `pypost/models/models.py`

Pydantic model that captures all data for one executed request:

| Field | Type | Notes |
|-------|------|-------|
| `id` | `str` | UUID, auto-generated |
| `timestamp` | `str` | UTC ISO-8601 with `Z` suffix |
| `method` | `str` | `GET`, `POST`, `MCP`, … |
| `url` | `str` | Fully rendered URL (Jinja2 variables substituted) |
| `headers` | `Dict[str, str]` | Rendered request headers |
| `body` | `str` | Rendered request body |
| `status_code` | `int` | HTTP status; `0` for network errors |
| `response_time_ms` | `float` | Round-trip time in milliseconds |
| `collection_name` | `Optional[str]` | `None` for ad-hoc requests |
| `request_name` | `Optional[str]` | `None` for ad-hoc requests |

---

### `HistoryManager` — `pypost/core/history_manager.py`

Thread-safe, Qt-independent store for history entries.

**Construction:**
```python
hm = HistoryManager(app_name="pypost", max_entries=500)
```
Loads `<user_data_dir>/pypost/history.json` on construction. A missing or corrupt file
results in an empty list and a `WARNING` log; the application continues normally.

**Public API:**

| Method | Description |
|--------|-------------|
| `get_entries() → List[HistoryEntry]` | Snapshot copy, newest-first |
| `append(entry) → None` | Prepend entry; enforce cap; async save |
| `delete_entry(entry_id) → None` | Remove by ID; async save |
| `clear() → None` | Remove all; async save |

**Thread safety:** All mutations acquire `self._lock`. The background write thread takes a
snapshot under the lock, then releases it before doing disk I/O, so the UI thread is never
blocked by file writes.

**Storage format:** `history.json` — a JSON array of `HistoryEntry.model_dump()` dicts,
written with `indent=2`, newest entry first.

---

### `RequestService` — `pypost/core/request_service.py`

History recording is opt-in via constructor injection:

```python
svc = RequestService(
    metrics=metrics,
    template_service=ts,
    history_manager=hm,   # pass None (default) to disable recording
)
```

`execute()` accepts two additional optional keyword arguments:

```python
result = svc.execute(
    request,
    variables=env_vars,
    collection_name="My API",   # stored in the history entry
    request_name="Login",       # stored in the history entry
)
```

History recording happens after the `ExecutionResult` is built. The entire block is wrapped in
`try/except Exception` so a recording failure never propagates to the caller.

---

### `RequestWorker` — `pypost/core/worker.py`

Passes `history_manager` and `collection_name` through to `RequestService`:

```python
worker = RequestWorker(
    request_data,
    variables=variables,
    metrics=metrics,
    history_manager=hm,
    collection_name=collection_name,
)
```

`request_name` is taken from `request_data.name` in `worker.run()`.

---

### `TabsPresenter` — `pypost/ui/presenters/tabs_presenter.py`

**New signal:**
```python
request_executed = Signal()   # emitted from _on_request_finished()
```
`MainWindow` connects this to `HistoryPanel.refresh()`.

**New slot:**
```python
def load_request_from_history(self, request_data: RequestData) -> None
```
Opens a new scratch tab pre-populated with the entry's `method`, `url`, `headers`, and `body`.
The request gets a fresh UUID and is not saved to any collection.

**`collection_name` resolution** happens in `_handle_send_request()` by calling
`self._request_manager.find_request(request_data.id)` before constructing the worker.

---

### `HistoryPanel` — `pypost/ui/widgets/history_panel.py`

Self-contained `QWidget` wired directly to `HistoryManager`.

**Signal:**
```python
load_into_editor = Signal(RequestData)
```

**Layout:** Filter input → vertical splitter (list / detail pane) → button row.

**Key behaviours:**
- `refresh()` re-reads `HistoryManager.get_entries()` and re-applies the current filter text.
- Context menu on list items exposes a **Delete** action.
- **Clear All** button shows a `QMessageBox.question` confirmation dialog before calling
  `HistoryManager.clear()`.
- Method icons are accepted via the `icons: dict | None` constructor parameter (same icon dict
  used by `MainWindow`). When `None`, the method is shown as plain text.

---

## Wiring in `MainWindow`

```python
# Instantiation (main_window.py __init__)
self.history_manager = HistoryManager()

self.tabs = TabsPresenter(
    ...,
    history_manager=self.history_manager,
)

# Layout (_build_layout)
self.history_panel = HistoryPanel(self.history_manager, icons=self.icons)
sidebar = QTabWidget()
sidebar.addTab(self.collections.widget, "Collections")
sidebar.addTab(self.history_panel, "History")
splitter.addWidget(sidebar)

# Signal wiring (_wire_signals)
self.tabs.request_executed.connect(self.history_panel.refresh)
self.history_panel.load_into_editor.connect(self.tabs.load_request_from_history)
```

---

## Configuration

| Setting | Default | How to change |
|---------|---------|---------------|
| Max history entries | `500` | Pass `max_entries=N` to `HistoryManager()` |
| Storage location | `<user_data_dir>/pypost/history.json` | Controlled by `platformdirs.user_data_dir` |

`user_data_dir` resolves to:
- **Linux:** `~/.local/share/pypost/`
- **macOS:** `~/Library/Application Support/pypost/`
- **Windows:** `%APPDATA%\pypost\`

---

## Observability

### Logging

| Logger | Level | Message key | Fields |
|--------|-------|-------------|--------|
| `pypost.core.history_manager` | DEBUG | `history_entry_appended` | `method`, `url`, `count` |
| `pypost.core.history_manager` | DEBUG | `history_entry_deleted` | `entry_id`, `remaining` |
| `pypost.core.history_manager` | DEBUG | `history_cleared` | `count` |
| `pypost.core.history_manager` | DEBUG | `history_manager_saved` | `count` |
| `pypost.core.history_manager` | WARNING | `history_manager_load_failed` | `path`, `error` |
| `pypost.core.request_service` | DEBUG | `history_entry_recorded` | `method`, `url`, `status`, `response_time_ms` |
| `pypost.core.request_service` | ERROR | `history_record_failed` | `error` |
| `pypost.ui.widgets.history_panel` | DEBUG | `history_panel_refreshed` | `entry_count` |
| `pypost.ui.widgets.history_panel` | INFO | `history_load_into_editor` | `method`, `url` |
| `pypost.ui.widgets.history_panel` | INFO | `history_cleared` | — |
| `pypost.ui.presenters.tabs_presenter` | INFO | `history_request_loaded_into_editor` | `method`, `url` |

### Prometheus Metrics

| Counter | Labels | Description |
|---------|--------|-------------|
| `history_entries_appended_total` | `method` | Incremented after every `HistoryManager.append()` |
| `history_entries_loaded_into_editor_total` | — | Incremented on each "Load into Editor" action |

Both counters are exposed via the existing metrics endpoint (`/metrics`).

---

## Tests

### `tests/test_history_manager.py`

| Test | What it verifies |
|------|-----------------|
| `test_load_missing_file` | Empty list when file does not exist |
| `test_load_corrupt_file` | Empty list + no crash on malformed JSON |
| `test_append_single_entry` | Entry is stored and retrievable |
| `test_append_enforces_cap` | 501 appends with `max_entries=500` → 500 entries, newest first |
| `test_get_entries_newest_first` | Prepend order is preserved |
| `test_delete_entry` | Correct entry removed by ID |
| `test_clear` | All entries removed |
| `test_save_and_reload` | Data survives a round-trip to disk |
| `test_concurrent_appends` | 50 concurrent threads produce 50 unique entries without corruption |

Run:
```bash
pytest tests/test_history_manager.py -v
```

### `tests/test_request_service.py` — history additions

| Test | What it verifies |
|------|-----------------|
| `test_history_entry_recorded_after_execute` | `append()` called once with correct fields |
| `test_history_records_resolved_url` | Template variables resolved before storing URL |
| `test_history_not_recorded_on_exception` | `append()` not called when HTTP client raises |
| `test_no_history_manager_no_error` | No exception when `history_manager=None` |
| `test_collection_name_propagated` | `collection_name` flows through to the entry |

Run:
```bash
pytest tests/test_request_service.py -v
```

---

## Known Limitations / Out of Scope

- Response body is **not** stored (disk-space concern; only request data + status/timing).
- Filtering supports URL substring only; method/status-code filtering is a future story.
- History is local; no cross-device sync or export.
- No UI-layer integration tests for `HistoryPanel` (requires a running `QApplication`).
