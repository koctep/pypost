# PYPOST-107: Body editor font via global theme

Related debt: [PYPOST-12](https://pypost.atlassian.net/browse/PYPOST-12)

## Goals

Request body editors should inherit application font size from the global theme (QSS +
`QApplication.setFont`) without presenter-level font propagation. Tab stops and the line-number
gutter must stay aligned when the user changes font size in Settings.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **user**, I want body editor text and gutter to scale when I change Application Font Size
  in Settings.
- As a **developer**, I want `CodeEditor` to react to inherited font changes so
  `TabsPresenter` does not maintain a per-tab font loop.

## Definition of Done

- [x] `CodeEditor` refreshes tab-stop distance and gutter width on `QEvent.FontChange`.
- [x] No manual `setFont` loop on body editors in `TabsPresenter.apply_settings`.
- [x] Regression test covers font-size change updating tab stops.
- [x] Developer docs describe body editor font inheritance.

## Task Description

PYPOST-106 centralized main-window font propagation. Body `CodeEditor` widgets still relied on
implicit inheritance but did not recalculate layout metrics when the global font changed.
This task makes the editor self-sufficient on font changes and removes misleading font
propagation wording from the tabs presenter.
