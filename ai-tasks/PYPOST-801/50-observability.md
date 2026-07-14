# PYPOST-801: Observability

## Events migrated

| Event | Level | Key fields | Module | Notes |
| --- | --- | --- | --- | --- |
| `app_startup` | INFO | — | `main` | Replaces `PyPost starting up` |
| `app_shutdown` | INFO | — | `main` | Replaces `PyPost shutting down` |

## Log format compliance

- snake_case event name as first token
- `%` formatting preserved (static strings — no variables)
- Logger name remains `pypost.main` (`logging.getLogger(__name__)`)
- Level unchanged (INFO)

## Operator impact

Log lines change from:

```text
... pypost.main INFO PyPost starting up
```

to:

```text
... pypost.main INFO app_startup
```

Grep/alert rules keyed on `PyPost starting` should update to `app_startup`.

## Catalog

`doc/dev/logging.md` Application lifecycle table updated; legacy migration section notes
PYPOST-801 completion.
