# PYPOST-754: Architecture — Background collection load at startup

## Context

- `EnvironmentStorageWorker` / `EnvironmentStorageGateway` (PYPOST-486) already offload
  encrypted environment I/O.
- `RequestManager.reload_collections()` is the sole disk-read path for collections.
- `MainWindow` currently constructs `RequestManager` (sync load) then `refresh_tree()`.

## Design

### New components

| Component | Role |
|-----------|------|
| `CollectionStorageWorker` | `QThread` running `storage.load_collections()` |
| `CollectionStorageGateway` | Single-flight async load, emits `load_completed` / `load_failed` |

### RequestManager changes

- `defer_initial_load: bool = False` on `__init__` — when `True`, skip `reload_collections()`.
- `apply_loaded_collections(collections)` — set in-memory list and rebuild index (no disk I/O).

### CollectionsPresenter changes

- Own `CollectionStorageGateway`.
- `load_collections_async()` — dispatch background load at startup.
- On `load_completed`: `apply_loaded_collections` → `refresh_tree` → emit `collections_loaded`.
- On `load_failed`: log error, emit `collections_loaded` with empty list (degraded empty tree).

### MainWindow startup gate

```text
load_collections_async()  ─┐
load_environments()       ─┼─► both ready → restore_tabs() + restore_tree_state()
```

Replace encryption-specific branching with unified `_maybe_complete_startup_restore()`.

## Data flow

```text
MainWindow.__init__
  RequestManager(defer_initial_load=True)   # empty memory
  collections.load_collections_async()
  env.load_environments()
        │
        ▼ (background thread)
CollectionStorageWorker.run → storage.load_collections()
        │
        ▼ (main thread signal)
Gateway.load_completed → RequestManager.apply_loaded_collections
                      → CollectionsPresenter.refresh_tree
                      → collections_loaded signal
        │
        ▼
MainWindow._maybe_complete_startup_restore (with env ready)
```

## Files to change

| File | Change |
|------|--------|
| `pypost/core/collection_storage_worker.py` | New |
| `pypost/core/collection_storage_gateway.py` | New |
| `pypost/core/request_manager.py` | defer flag + apply method |
| `pypost/ui/presenters/collections_presenter.py` | gateway + async load |
| `pypost/ui/main_window.py` | startup gate |
| `doc/dev/collection_loading.md` | Document async startup |
| `tests/test_collection_storage_*.py` | New tests |

## Out of scope

- User-triggered reload off main thread (PYPOST-757).
- Incremental tree updates (PYPOST-758).
