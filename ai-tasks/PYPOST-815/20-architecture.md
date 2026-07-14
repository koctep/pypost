# PYPOST-815: Architecture

## Problem

PYPOST-734 scoped mypy to `pypost/core/` and `pypost/models/` and excluded `pypost/ui/` via
`[[tool.mypy.overrides]]` `ignore_errors = true`. With core baseline debt reduced to 41 errors
(PYPOST-813/814), UI type-checking can enter the same incremental baseline workflow.

## Configuration

| Component | Role |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | `files` adds `pypost/ui`; removes `pypost.ui.*` override |
| `types-PySide6` | Community stub package for PySide6/Qt6 typing |
| `mypy-baseline.json` | Frozen `path:line:error-code` signatures (218 total) |
| `scripts/check_mypy_baseline.py` | Regex and paths extended for `pypost/ui/` |

## Baseline Gate

```
make typecheck
  └─ scripts/check_mypy_baseline.py
       └─ mypy pypost/core pypost/models pypost/ui
       └─ compare path:line:code set vs mypy-baseline.json
```

- **Pass:** current errors equal the committed baseline (exact match).
- **Fail:** new errors or resolved errors without baseline refresh.
- **Refresh:** `python scripts/check_mypy_baseline.py --update-baseline` after intentional fixes.

## Postponed annotations

Mechanical rollout (PYPOST-738 pattern) across all `pypost/ui/` modules:

- 57 modules received `from __future__ import annotations`.
- 10 modules already had the import.
- Blank line after future import when it is the first statement.

## Baseline Triage (2026-07-14)

218 errors total: 41 in `pypost/core/`, 0 in `pypost/models/`, 177 in `pypost/ui/` (29 files).

### UI error categories

| Error code | Count | Theme |
| --- | ---: | --- |
| `attr-defined` | 124 | Qt widget APIs, dynamic attributes, stub gaps |
| `misc` | 20 | Signal/slot typing, PySide6 stub edge cases |
| `no-any-return` | 10 | Untyped Qt method returns |
| `assignment` | 10 | Optional defaults, incompatible widget assignments |
| `override` | 6 | QWidget/QObject method override signatures |
| `arg-type` | 5 | `str \| None` vs `str`, enum arguments |
| `return-value` | 1 | Override return mismatch |
| `method-assign` | 1 | Monkey-patched method |

### Top UI files by error count

| File | Errors |
| --- | ---: |
| `pypost/ui/widgets/mixins.py` | 36 |
| `pypost/ui/collection_item_dialogs.py` | 26 |
| `pypost/ui/dialogs/hotkeys_dialog.py` | 12 |
| `pypost/ui/widgets/request_editor.py` | 11 |
| `pypost/ui/presenters/tabs_presenter_worker.py` | 9 |

**Suggested fix order:** (1) `mixins.py` hover helper Qt attribute guards, (2) dialog helpers in
`collection_item_dialogs.py`, (3) optional-parameter annotations in presenters, (4) QWidget
override signatures in delegates.

## Baseline impact

| Metric | Before (PYPOST-814) | After (PYPOST-815) |
| --- | ---: | ---: |
| Scoped paths | 2 | 3 |
| Total baseline errors | 41 | 218 |
| UI errors | 0 (ignored) | 177 |
| Core errors | 41 | 41 (unchanged) |
