# PYPOST-738: Code Cleanup

## Changes Reviewed

- Added `from __future__ import annotations` to 63 modules across `pypost/core/` and
  `pypost/models/`.
- Normalized blank line after future import when it is the first statement (38 files).

## Cleanup Actions

- Verified 100% coverage in both packages (0 modules missing the import).
- No unused imports introduced; no logic edits.
- Empty `__init__.py` files (`core/`, `core/qt/`, `core/key_sources/`, `models/`) updated.

## Result

Mechanical import-only diff. No dead code or formatting regressions expected.
