# PYPOST-1427: Dev Docs Notes

Updated `doc/dev/workspace_environment_variable_import.md`:

- Architecture diagram label for paged LRU model.
- `CollectionVariablesTableModel` section rewritten for chunk constants, sparse
  overlays, `cached_record_count`, and preset/cache invalidation behavior.
- Testing section entry for `tests/test_collection_variables_paged_model_repro.py`.

Run the paged repro suite:

```bash
make test PYTEST_ARGS="tests/test_collection_variables_paged_model_repro.py"
```
