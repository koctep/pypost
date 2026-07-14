# PYPOST-803: Collections/Tabs presenter font propagation closure

Parent: [PYPOST-68](https://pypost.atlassian.net/browse/PYPOST-68)
Source: PYPOST-43 TD-1 follow-up

## Goals

Close the remaining PYPOST-43 TD-1 gap for Collections and Tabs presenters. After
PYPOST-106 and PYPOST-425, application font size propagates globally; presenters must
not reintroduce redundant per-widget font loops.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **developer**, I want a clear decision on whether Collections/Tabs presenters need
  `apply_font`, so the presenter layer stays consistent with EnvPresenter (PYPOST-425).
- As a **user**, I want font size from Settings to apply to the collections tree and
  request tabs without manual per-widget wiring.

## Definition of Done

- [x] Decision documented: closure via global font propagation (no `apply_font` added).
- [x] Regression tests prove presenter widgets inherit application font after
  `StyleManager.apply_appearance`.
- [x] Developer docs updated (`doc/dev/ui_font_and_styles.md`).
- [x] PYPOST-68 TD-1 marked resolved in tech-debt artifacts.
- [x] `make check` passes.

## Task Description

PYPOST-43 TD-1 originally recommended thin `apply_font` methods on each presenter so
`MainWindow` would not reach into internal widgets. PYPOST-68 added `apply_font` on
`EnvPresenter`; PYPOST-425 removed it as redundant once global QSS and
`QApplication.setFont` handled propagation. This task resolves the same question for
`CollectionsPresenter` and `TabsPresenter`.

## Q&A

- **Why not add `apply_font`?** PYPOST-425 established the project pattern: global
  appearance via `StyleManager.apply_appearance` is sufficient; explicit presenter loops
  drift as widgets are added.
- **How is encapsulation preserved?** `MainWindow.apply_settings` already delegates to
  `style_manager.apply_appearance` and presenter `apply_settings` (indent/colors only);
  it never calls `setFont` on presenter internals.
