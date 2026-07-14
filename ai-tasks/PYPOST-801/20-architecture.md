# PYPOST-801: Architecture

## Change summary

Two INFO log lines in `pypost/main.py` `main()`:

| Location | Before (Pattern C) | After |
| --- | --- | --- |
| Start of `main()` | `PyPost starting up` | `app_startup` |
| Before `metrics_manager.stop_server()` | `PyPost shutting down` | `app_shutdown` |

Event names match Pattern C migration table in `doc/dev/logging.md`. No key=value fields
required — lifecycle bookends have no variable context.

## Affected files

| File | Change |
| --- | --- |
| `pypost/main.py` | Two `logger.info` message strings |
| `doc/dev/logging.md` | Catalog + legacy migration note |

## Tests

No existing tests assert these message strings. Full `make check` sufficient.

## Risks

None — INFO-level rename only; no behavioral or API change.
