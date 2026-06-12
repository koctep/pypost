# PYPOST-65: Duplicate QPoint import in history_panel

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-41 TD-8: remove the redundant second `from PySide6.QtCore import QPoint`
statement in `history_panel.py` by merging `QPoint` into the primary QtCore import.

## Problem statement

`HistoryPanel._on_context_menu` uses `QPoint` for the context-menu position. The module had
two separate `from PySide6.QtCore import` lines — one for `Qt, Signal` and a second for
`QPoint` — which violates import hygiene and triggers lint noise.

## User stories

- As a **developer**, I want a single consolidated QtCore import so the module header is easy
  to scan and consistent with the rest of the codebase.

## Functional requirements

- **FR-1:** `history_panel.py` has exactly one `from PySide6.QtCore import` statement.
- **FR-2:** `QPoint`, `Qt`, and `Signal` remain available; `_on_context_menu` behavior unchanged.

## Non-functional requirements

- **NFR-1:** Minimal diff — import consolidation only; no logic changes.
- **NFR-2:** Existing history panel tests pass.

## Out of scope

- Refactoring other widgets with similar import patterns.
- Changing context-menu behavior or UI layout.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | No duplicate `from PySide6.QtCore import` in `history_panel.py` |
| AC-2 | `QPoint` imported alongside `Qt` and `Signal` on one line |
| AC-3 | `tests/test_history_panel.py` passes |
