# PYPOST-738: Developer Documentation

## Updates

| File | Change |
| --- | --- |
| `doc/dev/static_type_checking.md` | Added **Postponed annotations convention** section |

## Key Points for Maintainers

- All `pypost/core/` and `pypost/models/` modules now use
  `from __future__ import annotations`.
- Place the import after module docstrings, before other imports, with a blank line after.
- New modules in these packages must include the future import.
- UI layer (`pypost/ui/`) is not yet covered — follow-up debt item.

## Related Docs

- [static_type_checking.md](../../doc/dev/static_type_checking.md) — mypy and typing conventions
- [maintainability_audit.md](../../doc/dev/maintainability_audit.md) — R-P3-002 origin
