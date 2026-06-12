# PYPOST-127: Code Cleanup

## Lint and format

- No new lint issues in `request_manager.py` or `test_request_manager.py`.
- Existing module style preserved (logging, type hints, private helpers).

## Review notes

- `rename_request` simplified to use `_request_index.get` instead of nested loops.
- Removed unnecessary `_rebuild_index()` call on rename (ID unchanged).

## Files touched

- `pypost/core/request_manager.py`
- `tests/test_request_manager.py`
- `doc/dev/collection_loading.md`
- `ai-tasks/PYPOST-14/40-tech-debt.md`
