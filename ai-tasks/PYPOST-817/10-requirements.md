# PYPOST-817: Expand postponed annotations to pypost/ui/ (R-P3-002 UI)

## Summary

Follow-up from [PYPOST-738](https://pypost.atlassian.net/browse/PYPOST-738) (R-P3-002). PYPOST-738
rolled out `from __future__ import annotations` across `pypost/core/` and `pypost/models/` but
left `pypost/ui/` out of scope. This task completes the UI portion of the postponed-annotations
convention.

## Supersession

Bulk implementation was already delivered in
[PYPOST-815](https://pypost.atlassian.net/browse/PYPOST-815) as part of the mypy UI baseline
scope (57 modules received the import; 10 already had it). PYPOST-817 verifies closure and
documents supersession rather than re-applying the migration.

## Acceptance Criteria

1. Every `.py` file under `pypost/ui/` includes `from __future__ import annotations`.
2. Import is placed after an optional module docstring, before other imports, with a blank line
   after when followed by other imports.
3. Convention documented in `doc/dev/static_type_checking.md` (UI scope complete).
4. `make check` passes.
5. Task artifacts record verification counts and PYPOST-815 supersession.

## Out of Scope

- Adding or fixing type hints beyond the future import.
- Fixing UI mypy baseline errors (tracked under PYPOST-734 / PYPOST-815).
- Enabling mypy in CI or `make check`.

## User Stories

- As a **maintainer**, I want all UI modules to use postponed annotations, so that type hints stay
  consistent with core and models.
- As a **contributor**, I want the convention documented, so that new UI modules follow the same
  import pattern from the first commit.
