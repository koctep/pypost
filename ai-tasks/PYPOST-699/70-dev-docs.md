# PYPOST-699: Developer Documentation

## Summary

Removed the unused `pypost/utils/` package and updated architecture docs so the directory
tree and audit findings match the codebase.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/architecture.md` | Removed `utils/` from directory tree |
| `doc/dev/architecture_audit.md` | L-006 remediated; R-P3-001 marked Done |

## Deleted

| Path | Reason |
| --- | --- |
| `pypost/utils/__init__.py` | Empty package, no importers |

## Guidance for future shared helpers

Add helpers next to their domain package (`core/`, `ui/`) rather than reviving a generic
`utils/` root. Introduce a shared module only when at least two call sites need it.
