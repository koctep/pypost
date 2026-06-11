# PYPOST-327: Architecture

## Approach

Use `{collection.id}.json` as the canonical on-disk filename in `StorageManager`.

## Components

| Component | Change |
|-----------|--------|
| `StorageManager.save_collection` | Write to `{id}.json`; remove legacy `{name}.json` if present |
| `StorageManager.delete_collection` | Delete by ID; optional legacy name cleanup |
| `StorageManager.load_collections` | Detect legacy name-based files and migrate to ID path |
| `RequestManager.rename_collection` | Save only — no delete+recreate file dance |
| `RequestManager.delete_collection` | Pass collection ID to storage |

## Migration

On load, if filename stem equals `collection.name` but not `collection.id`, copy content to
ID path and remove the legacy file.

## Out of scope

- Collision policy for duplicate display names (PYPOST-350)
- GUI integration tests (PYPOST-338, PYPOST-348)
