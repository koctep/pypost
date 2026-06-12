# Collection Storage

## Filename convention

Each collection is persisted as a JSON file under the user data `collections/` directory.
The filename is `{collection.id}.json` — the stable UUID, not the display name.

This decouples persistence identity from rename operations and prevents same-name
collections from overwriting each other's files.

## API

Consumers type-hint against `StorageInterface` (`pypost/core/storage_interface.py`).
`StorageManager` is the production implementation; tests use `FakeStorageManager` or
`MagicMock(spec=StorageInterface)`.

### `StorageManager.save_collection(collection)`

Writes `collection` to `{id}.json`. If a legacy name-based file exists for the same
collection, it is removed after save.

### `StorageManager.delete_collection(collection_id, *, collection_name=None)`

Removes the ID-based file. When `collection_name` is provided, also removes a legacy
name-based file if present.

### `StorageManager.load_collections()`

Loads all `*.json` files. Legacy files whose stem equals `collection.name` (but not
`collection.id`) are migrated to the ID path and the old file is deleted.

## Rename behavior

`RequestManager.rename_collection` updates the `name` field in JSON and calls
`save_collection`. The on-disk filename does not change.

## Duplicate display names

`RequestManager.create_collection` and `rename_collection` reject duplicate
collection display names. Persistence uses collection IDs, so same-name collections
would not overwrite each other on disk, but the UI enforces unique names for clarity.
