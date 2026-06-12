# PYPOST-50: Code Cleanup

## Summary

Type-hint refactor only. No formatting churn beyond new module and consumer imports.

## Checklist

- [x] New module follows `http_client_protocol.py` conventions (`@runtime_checkable`, docstring).
- [x] Imports use `StorageInterface` from `storage_interface`, not re-exported from `storage`.
- [x] `FakeStorageManager` stubs return `EnvironmentSerializeStats()` for save helpers.
- [x] No unused imports left in updated consumer modules.
- [x] Line length within 100 characters.

## Notes

`MainWindow` still imports `StorageManager` — intentional composition-root wiring.
