# PYPOST-70: RequestTab.layout shadows QWidget.layout()

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-43 TD-5: `RequestTab` must not assign an instance attribute named `layout`, which
shadows `QWidget.layout()` and breaks Qt's layout introspection API.

## Problem statement

`RequestTab.__init__` sets `self.layout = QVBoxLayout(self)`. `QWidget` already exposes
`layout()` as a method. The instance attribute replaces the bound method on that instance, so
`tab.layout()` fails or behaves unexpectedly when Qt or application code queries the widget
layout.

## User stories

- As a **developer maintaining the Qt UI layer**, I want `RequestTab` to follow Qt naming
  conventions so layout queries and future refactors do not hit shadowed APIs.
- As a **contributor writing tests or tooling**, I expect `tab.layout()` to return the tab's
  `QVBoxLayout` like any other `QWidget`.

## Functional requirements

- **FR-1:** `RequestTab` must not store a `layout` instance attribute.
- **FR-2:** `RequestTab.layout()` must return the root vertical layout (unchanged visual
  structure).
- **FR-3:** Tab UI composition (request editor + response splitter) remains unchanged.

## Non-functional requirements

- **NFR-1:** Minimal diff; rename only, no behavioral change.
- **NFR-2:** Regression test proves `layout()` is callable and no instance attribute shadows it.

## Out of scope

- Refactoring other widgets that use `self.layout` (e.g. settings dialog).
- Broader `RequestTab` API changes.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | No `self.layout` assignment on `RequestTab` |
| AC-2 | `tab.layout()` returns the tab's `QVBoxLayout` |
| AC-3 | Existing tab presenter and integration tests pass |
| AC-4 | Regression test covers layout method accessibility |
