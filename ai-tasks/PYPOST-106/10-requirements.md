# PYPOST-106: Manual Font Propagation in MainWindow.apply_settings

Related debt: [PYPOST-12](https://pypost.atlassian.net/browse/PYPOST-12)

## Goals

When users change application font size in Settings, every part of the main window should reflect
that size without maintaining a fragile list of individual widgets. The UI should stay readable
and consistent as new controls are added.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **user**, I want font size from Settings to apply across the main window (collections,
  tabs, environment bar, menus) without visible inconsistencies.
- As a **developer**, I want font propagation to rely on Qt application-level mechanisms (default
  font and global stylesheet) so new widgets do not require manual updates in `apply_settings`.

## Definition of Done

- [x] `MainWindow.apply_settings` no longer loops over named widgets to call `setFont`.
- [x] Font size is propagated via `QApplication` default font and/or global QSS.
- [x] Existing font-size regression tests pass (`test_apply_settings_font.py`).
- [x] Stylesheet application order remains correct (stylesheet before `app.setFont` — PYPOST-404).
- [x] Developer documentation describes the font + stylesheet approach.

## Task Description

PYPOST-12 introduced manual font propagation because automatic inheritance from `QApplication`
was insufficient after global stylesheet application. This task replaces that maintenance burden
with a centralized approach: inject `font-size` into the application stylesheet and keep
`QApplication.setFont` as the default for unstyled widgets.

## Q&A

- **Why keep `app.setFont` if QSS sets font-size?**
  Belt-and-suspenders: QSS covers styled widgets; app font covers widgets without explicit rules
  and matches Qt conventions after stylesheet re-polish (PYPOST-404).
- **Do dialogs need changes?**
  Out of scope; they are separate windows. Follow-up if inconsistent sizing is reported.
