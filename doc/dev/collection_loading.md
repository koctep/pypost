# Collection Loading

## Overview

Collection data in the running application flows through `RequestManager`. The UI never reads
collection JSON from `StorageManager` directly. This pattern resolves PYPOST-40 audit
recommendation R5 ([PYPOST-47](https://pypost.atlassian.net/browse/PYPOST-47)).

## Architecture

```text
StorageManager.load_collections()
        ↓ (only via RequestManager)
RequestManager.collections  +  _request_index
        ↓ get_collections()
CollectionsPresenter.refresh_tree()  →  QTreeView model
```

- **RequestManager** owns the in-memory collection list and request index
  (`_request_index: dict[str, tuple[RequestData, Collection]]`). `find_request` and
  `rename_request` use the index for O(1) lookup; `reload_collections` and `save_request`
  rebuild it; delete paths drop keys incrementally ([PYPOST-127](https://pypost.atlassian.net/browse/PYPOST-127)).
- **RequestManager** is the only component that calls `StorageManager.load_collections()`
  for normal operation.
- **CollectionsPresenter** renders the sidebar tree. It reads via `get_collections()` and
  rebuilds the Qt model in `refresh_tree()`.

## API / Usage

### `RequestManager.reload_collections()`

Re-reads all collection JSON from disk and rebuilds the request index. Called automatically in
`RequestManager.__init__` unless `defer_initial_load=True` (MainWindow startup path).

### `RequestManager.apply_loaded_collections(collections)`

Sets in-memory collections and rebuilds the request index from a list loaded on a background
thread. Used by `CollectionStorageGateway` at startup; does not touch disk.

### `RequestManager.get_collections() -> list[Collection]`

Returns the current in-memory collection list. **Use this for all UI reads** (tree, env MCP
request discovery via injected callable, tab save-as dialogs).

### `CollectionsPresenter.refresh_tree()`

Clears and repopulates the tree model from `get_collections()` without touching disk. Use after
in-app CRUD or tab save when RequestManager memory is already up to date.

### `CollectionsPresenter.load_collections()`

When a `CollectionStorageGateway` is configured (production `MainWindow`), dispatches an
async disk reload and skips if a load is already in progress. Otherwise falls back to
synchronous `reload_collections()` + `refresh_tree()` (unit tests).

### `CollectionsPresenter.add_saved_request_to_tree(request, collection_id)`

Inserts one saved request node under an existing collection, or appends a new collection row when
the target collection is not yet in the tree. Use after save-as when RequestManager memory is
already current ([PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319)).

## MainWindow wiring

- **Startup:** `RequestManager(defer_initial_load=True)`; `CollectionsPresenter.load_collections_async()`
  loads JSON on a background thread via `CollectionStorageGateway`. MainWindow waits for both
  `collections_loaded` and `environments_loaded` before `restore_tabs()` and
  `restore_tree_state()`.
- **After tab save:** `TabsPresenter.request_saved` → `collections.refresh_tree()` (save already
  updated RequestManager memory).
- **After save-as:** `TabsPresenter.request_save_as_completed` →
  `collections.add_saved_request_to_tree()` (incremental insert; no full tree rebuild).

## Async startup (PYPOST-754)

```text
CollectionStorageWorker (QThread)
  → storage.load_collections()
CollectionStorageGateway.load_completed
  → RequestManager.apply_loaded_collections()
  → CollectionsPresenter.refresh_tree()
  → collections_loaded signal
```

User-triggered reload uses the same `CollectionStorageGateway` as startup (PYPOST-757).

### Worker finish teardown (PYPOST-829)

`CollectionStorageGateway._on_worker_finished` matches the env gateway hygiene:

1. Capture finished worker; clear `self._worker`.
2. `deleteLater()` + short `wait(100)` (`_WORKER_FINISH_WAIT_MS`).
3. If `_pending_load`, start a **new** worker via `_start_load`.

Module: `pypost/core/qt/collection_storage_gateway.py`. Same rationale as
[Async Environment Storage](environment_storage_async.md) § Worker finish teardown —
avoids premature `QThread` destruction under rapid churn + GC.

## Configuration

No configuration flags. Collection files live under the user data `collections/` directory; see
[collection_storage.md](collection_storage.md).

## Observability

Gateway lifecycle logs (DEBUG/INFO for queue and pending restart) live on
`collection_storage_gateway_*`. Worker finish hygiene (PYPOST-829):

- `collection_storage_gateway_worker_finish_wait_timeout` (WARNING) —
  `wait_ms`, `pending_load` — short join after `finished` timed out.
  Happy-path finish is not logged.

See `ai-tasks/PYPOST-829/50-observability.md` and [Logging](logging.md).

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Tree stale after manual JSON edit on disk | Memory not reloaded | Call `load_collections()` or restart app |
| Tree wrong after save | Bug in RequestManager CRUD | Check `save_request` / index rebuild |
| Double disk read on startup | Calling `load_collections()` at startup | Use `refresh_tree()` instead |
| `collection_storage_gateway_worker_finish_wait_timeout` | Native cleanup past 100 ms after `finished` | Triage pending flag; do not use unbounded GUI `wait()` |
| Segfault in `_on_worker_finished` under churn | Historical H3 (pre-PYPOST-829) | Run `tests/test_storage_gateway_h3_stress.py` |

## Tests

H3 canary (shared with env gateway):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_storage_gateway_h3_stress.py -v
```

Gateway / worker unit modules:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_collection_storage_gateway.py \
  tests/test_collection_storage_worker.py
```

## Performance

For a full vs incremental tree refresh inventory (audit closure
[PYPOST-383](https://pypost.atlassian.net/browse/PYPOST-383)), see
[collection_tree_performance.md](collection_tree_performance.md).

## Related

- [Collection Tree Performance](collection_tree_performance.md)
- [Collection Storage](collection_storage.md)
- [Async Environment Storage](environment_storage_async.md) — shared gateway finish teardown
- [Architecture Overview](architecture.md)
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)
