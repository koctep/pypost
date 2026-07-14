# PYPOST-738: Expand postponed annotations (R-P3-002)

## Goals

Follow-up from PYPOST-687 maintainability audit (R-P3-002). Only ~16% of PyPost modules used
postponed evaluation of annotations (`from __future__ import annotations`). Expanding adoption in
the domain layers (`pypost/core/`, `pypost/models/`) improves forward-reference ergonomics and
aligns with mypy incremental typing (PYPOST-734).

## User Stories

- As a **maintainer**, I want all core and models modules to use postponed annotations, so that
  type hints stay consistent and forward references work without string quotes.
- As a **contributor**, I want the convention documented, so that new modules in core/models follow
  the same import pattern.

## Definition of Done

- [x] Every `.py` file under `pypost/core/` includes `from __future__ import annotations`.
- [x] Every `.py` file under `pypost/models/` includes `from __future__ import annotations`.
- [x] Import placed after module docstring (when present), before other imports, with blank line
  after.
- [x] `make check` passes (no behavior change).
- [x] Convention documented in `doc/dev/static_type_checking.md`.

## Task Description

Mechanical hygiene task — add one import line per module. No runtime logic changes. UI layer
(`pypost/ui/`) remains out of scope for this debt item.

Implementation: Python (PyPost core and models).

## Out of Scope

- Adding or fixing type hints beyond the future import
- `pypost/ui/` modules
- Enabling mypy in CI
- Updating `mypy-baseline.json`

## Q&A

- **Q**: Does this change runtime behavior?
- **A**: No — annotations are already stored unevaluated at runtime in most cases; this makes
  behavior explicit and consistent.
- **Q**: Why core/models only?
- **A**: These packages are mypy-scoped (PYPOST-734) and have the highest type-hint density.
