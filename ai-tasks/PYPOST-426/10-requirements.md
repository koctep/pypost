# PYPOST-426: apply_settings accepts settings as a plain positional argument

Related debt: [PYPOST-404](https://pypost.atlassian.net/browse/PYPOST-404)

## Goals

Improve maintainability and static-analysis coverage for the settings application path so
developers and tooling can rely on consistent typing across presenters and the main window.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **developer**, I want `MainWindow.apply_settings` to declare `AppSettings` so IDEs and
  type checkers catch incorrect call sites.
- As a **maintainer**, I want the signature to match `TabsPresenter.apply_settings` and
  `EnvPresenter.apply_settings` for a uniform API.

## Definition of Done

- [x] `MainWindow.apply_settings` parameter is annotated as `AppSettings`.
- [x] Import of `AppSettings` added in `main_window.py`.
- [x] Existing tests pass (no behavior change).
- [x] Developer docs reflect the typed signature.

## Task Description

PYPOST-404 review (TD-2) noted `def apply_settings(self, settings) -> None` lacks a type
annotation. Only `AppSettings` is ever passed; sibling presenters already use
`settings: AppSettings`.

## Q&A

- **Keyword-only vs typed positional?**
  Presenters use typed positional `settings: AppSettings`; main window follows the same pattern
  for consistency (no `*` keyword-only separator needed).
