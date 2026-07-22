# PYPOST-881: Developer Documentation

## Updates

| Doc | Change |
| --- | --- |
| `doc/dev/environment_storage_async.md` | Note that finish teardown stays inline until a third consumer or real drift (PYPOST-881 YAGNI deferral) |
| `doc/dev/collection_loading.md` | Same deferral note for collection gateway finish teardown |

## Review

Self-review against `70-dev-docs.mdc`: overview/architecture for finish
teardown already present from PYPOST-829; usage unchanged; added
maintainer guidance on when *not* to extract a shared helper; troubleshooting
unchanged.
