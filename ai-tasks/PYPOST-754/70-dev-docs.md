# PYPOST-754: Dev Docs

## Summary

Startup collection loading now runs off the main thread. See
[collection_loading.md](../../doc/dev/collection_loading.md) — sections **Async startup
(PYPOST-754)** and updated **MainWindow wiring**.

## Key APIs

- `RequestManager(..., defer_initial_load=True)` — skip sync disk read in constructor.
- `RequestManager.apply_loaded_collections(collections)` — apply background load result.
- `CollectionsPresenter.load_collections_async()` — startup dispatch.
- `CollectionsPresenter.collections_loaded` — signal when tree is ready.

## Related

- [Environment Storage Async](../../doc/dev/environment_storage_async.md) — pattern reference.
- [Performance Audit](../../doc/dev/performance_audit.md) — R-P1-002 finding.
