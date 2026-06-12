# PYPOST-112: Font inheritance investigation and apply_settings cleanup

Related debt: [PYPOST-12](https://pypost.atlassian.net/browse/PYPOST-12)

## Goals

Understand why Qt font inheritance failed for parts of the main window and confirm that
`MainWindow.apply_settings` uses a maintainable, centralized font propagation approach instead
of manual per-widget updates.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **user**, I want application font size from Settings to apply consistently across the
  main window without visible mismatches between panels, tabs, and menus.
- As a **developer**, I want a documented explanation of font inheritance behaviour so new UI
  controls inherit size without editing `apply_settings` widget lists.

## Definition of Done

- [x] Root causes of font inheritance gaps are documented (stylesheet re-polish, widget-local
  QSS, editor metric refresh).
- [x] `MainWindow.apply_settings` uses global QSS + `QApplication.setFont` with no per-widget
  `setFont` loop.
- [x] Body editor font metrics on theme change are handled (PYPOST-107 verified).
- [x] Regression tests for font application pass (`test_apply_settings_font.py`,
  `test_style_manager_font.py`).
- [x] Developer documentation updated with investigation findings.
- [x] PYPOST-12 tech-debt entry marked resolved.

## Task Description

PYPOST-12 introduced manual font propagation in `MainWindow.apply_settings` because automatic
inheritance from `QApplication` was unreliable after global stylesheet application. This task
investigates those reasons and confirms or completes the refactor toward global QSS. Prior work
in PYPOST-106 and PYPOST-107 may already satisfy most acceptance criteria; this task verifies
and closes the debt item.

## Q&A

- **Does this duplicate PYPOST-106?**
  PYPOST-106 implemented the global QSS refactor. PYPOST-112 closes the original PYPOST-12
  follow-up by documenting why inheritance failed and confirming the solution is complete.
- **What about dialogs and special widgets?**
  Out of scope unless they block main-window font consistency. Hardcoded widget-level `font-size`
  remains optional UX polish (see PYPOST-106 follow-up).
