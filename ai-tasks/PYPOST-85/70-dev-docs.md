# PYPOST-85: Developer Documentation

## FakeStorageManager.seed_collections

Use `seed_collections(collections)` in tests when `RequestManager` was constructed with an
initially empty fake and you need to simulate data appearing on disk **before** a later
`reload_collections()` call.

Do **not** assign to `storage._collections` from tests; that couples assertions to private
implementation details.

## Related

- `load_collections()` returns `list(self._collections)`.
- Constructor `FakeStorageManager([...])` is still appropriate when the manager should load
  data on first `reload` inside `RequestManager.__init__`.
