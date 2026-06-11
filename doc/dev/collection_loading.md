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

- **RequestManager** owns the in-memory collection list and request index. It is the only
  component that calls `StorageManager.load_collections()` for normal operation.
- **CollectionsPresenter** renders the sidebar tree. It reads via `get_collections()` and
  rebuilds the Qt model in `refresh_tree()`.

## API / Usage

### `RequestManager.reload_collections()`

Re-reads all collection JSON from disk and rebuilds the request index. Called automatically in
`RequestManager.__init__`. Use when disk content may have changed outside the manager (e.g.
future manual refresh action).

### `RequestManager.get_collections() -> list[Collection]`

Returns the current in-memory collection list. **Use this for all UI reads** (tree, env MCP
request discovery via injected callable, tab save-as dialogs).

### `CollectionsPresenter.refresh_tree()`

Clears and repopulates the tree model from `get_collections()` without touching disk. Use after
in-app CRUD or tab save when RequestManager memory is already up to date.

### `CollectionsPresenter.load_collections()`

Calls `reload_collections()` then `refresh_tree()`. Full resync from disk plus UI rebuild.

## MainWindow wiring

- **Startup:** `RequestManager` loads in `__init__`; MainWindow calls
  `collections.refresh_tree()` once (no double reload).
- **After tab save:** `TabsPresenter.request_saved` → `collections.refresh_tree()` (save already
  updated RequestManager memory).

## Configuration

No configuration flags. Collection files live under the user data `collections/` directory; see
[collection_storage.md](collection_storage.md).

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Tree stale after manual JSON edit on disk | Memory not reloaded | Call `load_collections()` or restart app |
| Tree wrong after save | Bug in RequestManager CRUD | Check `save_request` / index rebuild |
| Double disk read on startup | Calling `load_collections()` at startup | Use `refresh_tree()` instead |

## Related

- [Collection Storage](collection_storage.md)
- [Architecture Overview](architecture.md)
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)
