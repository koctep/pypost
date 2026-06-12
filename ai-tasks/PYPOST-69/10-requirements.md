# PYPOST-69: Unused Environment import in tabs_presenter

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-43 TD-4: remove the unused `Environment` import from
`tabs_presenter.py` so the module header reflects only symbols that are actually
used.

## Problem statement

`TabsPresenter` imports `Environment` from `pypost.models.models` but never
references it. The import is an artefact from the original `MainWindow`
decomposition (PYPOST-43) and triggers lint noise.

## User stories

- As a **developer**, I want `tabs_presenter.py` to import only used symbols so
  the module is easy to scan and consistent with import hygiene across the
  codebase.

## Functional requirements

- **FR-1:** `tabs_presenter.py` does not import `Environment`.
- **FR-2:** `RequestData` and all presenter behavior remain unchanged.

## Non-functional requirements

- **NFR-1:** Minimal diff — import removal only; no logic changes.
- **NFR-2:** Existing tabs presenter tests pass.

## Out of scope

- Refactoring other presenters with similar unused imports.
- Changing tab or environment propagation behavior.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | No `Environment` import in `tabs_presenter.py` |
| AC-2 | `from pypost.models.models import RequestData` (no trailing symbols) |
| AC-3 | `tests/test_tabs_presenter.py` passes |
| AC-4 | `flake8 pypost/ui/presenters/tabs_presenter.py` passes |
