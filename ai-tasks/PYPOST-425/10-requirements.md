# PYPOST-425: Remove redundant explicit widget font loops

Related: [PYPOST-404](https://pypost.atlassian.net/browse/PYPOST-404) TD-1,
[PYPOST-106](https://pypost.atlassian.net/browse/PYPOST-106)

## Goals

After PYPOST-404 and PYPOST-106, application font size is propagated globally via QSS
(`QWidget { font-size: Npt; }`) and `QApplication.setFont`. Explicit per-widget `setFont`
loops are redundant belt-and-suspenders that drift as the UI grows.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **developer**, I want font propagation centralized so new widgets inherit size without
  maintaining hardcoded widget lists.
- As a **user**, I want font size from Settings to remain consistent across the main window
  and environment bar after this cleanup.

## Definition of Done

- [x] No explicit per-widget `setFont` loop in `MainWindow.apply_settings` (already removed
  in PYPOST-106; verified).
- [x] No explicit per-widget `setFont` loop in `EnvPresenter` (`apply_font` removed).
- [x] Font regression tests pass (`test_apply_settings_font.py`).
- [x] Env presenter tests updated (removed `apply_font` coverage).
- [x] Developer docs reflect global font propagation only.

## Task Description

PYPOST-404 review (TD-1) flagged the main-window widget loop as redundant once
`app.setFont` runs after `apply_styles`. PYPOST-106 removed that loop and added global QSS.
`EnvPresenter.apply_font` remained as the same pattern; this task removes it and stale test
references.

## Q&A

- **Is `app.setFont` still needed?** Yes — complements QSS for widgets without explicit
  rules and survives the PYPOST-404 call-order fix.
- **What about code editors / hotkeys dialog?** Out of scope; they use local font rules for
  monospace or table layout.
