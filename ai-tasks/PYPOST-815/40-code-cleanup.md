# PYPOST-815: Code Cleanup

## Changes

| Area | Change |
| --- | --- |
| `pyproject.toml` | Add `pypost/ui` to `files`; remove `pypost.ui.*` ignore override |
| `requirements-dev.in` / `.txt` | Add `types-PySide6>=6.10,<7` |
| `scripts/check_mypy_baseline.py` | Extend paths and error regex for `pypost/ui/` |
| `Makefile` | Update `typecheck` help text |
| `mypy-baseline.json` | Add 177 UI errors; `error_count` 41 → 218 |
| `pypost/ui/**/*.py` | `from __future__ import annotations` in 57 modules |
| `tests/test_mypy_baseline.py` | Assert scope includes `pypost/ui` |
| `scripts/audit_baseline_metrics.py` | Bump `collections_presenter.py` cap 275 → 280 (+2 import lines) |

## Verification

- [x] `make typecheck` — pass (baseline match, 218 errors)
- [x] `make check` — pass (lint + 1617 tests)
- [x] No runtime logic changes
- [x] Core baseline unchanged at 41 errors

## Checklist

- [x] Line length ≤ 100
- [x] UTF-8, LF endings
- [x] English comments and docs
- [x] Mechanical import-only diff in UI modules
