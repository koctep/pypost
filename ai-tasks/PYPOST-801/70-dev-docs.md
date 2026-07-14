# PYPOST-801: Developer Documentation

## Summary

Updated `doc/dev/logging.md` to reflect migrated startup/shutdown events in `main.py`.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/logging.md` | Application lifecycle catalog: `app_startup`, `app_shutdown`; legacy migration note |

## Documentation Highlights

- `app_startup` and `app_shutdown` listed under Application lifecycle (no longer marked legacy).
- Pattern C migration section references PYPOST-801 for `main.py` completion.
- Preferred event names match implementation in `pypost/main.py`.

## Verification

- Catalog entries match `logger.info` calls in `main.py`.
- No stale `PyPost starting up` / `PyPost shutting down` in Application lifecycle table.
