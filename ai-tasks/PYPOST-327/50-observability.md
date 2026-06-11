# PYPOST-327: Observability

Added structured log events:

- `storage_collection_legacy_file_removed` — legacy name file cleaned after ID-based save
- `storage_collection_migrated` — legacy name file migrated to ID path on load

Existing `storage_collection_load_failed` warning retained for corrupt files.
