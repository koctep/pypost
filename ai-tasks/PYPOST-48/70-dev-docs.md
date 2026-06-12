# PYPOST-48 — Developer Documentation

## Summary

`RequestManager.delete_collection_item` and `rename_collection_item` dispatch through a strategy
registry in `collection_item_strategies.py` instead of inline `item_type` branching.

## Files updated

| File | Purpose |
| --- | --- |
| `pypost/core/collection_item_strategies.py` | `CollectionItemStrategy` + default registry |
| `pypost/core/request_manager.py` | Optional `item_strategies` injection |
| `tests/test_collection_item_strategies.py` | Custom strategy injection tests |
| `doc/dev/testability.md` | Collection item strategy section |
| `doc/dev/tech-debt/PYPOST-40.md` | R6 marked resolved |

## Testing

```bash
make test TESTS=tests/test_collection_item_strategies.py tests/test_request_manager_delete.py
```

## Related

- [PYPOST-40](https://pypost.atlassian.net/browse/PYPOST-40) — SOLID audit (R6)
- [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) — protocol pattern precedent
