# PYPOST-61: QTabWidget module-level import in main_window

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-41 TD-4: align `QTabWidget` import style in `main_window.py` with other Qt
imports at module scope.

## Problem statement

`from PySide6.QtWidgets import QTabWidget` lives inside `_build_layout()` while every other
Qt widget import is at the top of the file. Deferred imports obscure the module dependency
graph and can hide unused-import or ordering issues from static analysis tools.

## User stories

- As a **developer reading `main_window.py`**, I want all Qt widget imports in one place so I
  can see dependencies at a glance.
- As a **maintainer running linters**, I want imports at module level so tools like ruff catch
  issues consistently.

## Functional requirements

- **FR-1:** `QTabWidget` is imported in the top-level `from PySide6.QtWidgets import (...)` block.
- **FR-2:** No deferred import of `QTabWidget` remains inside `_build_layout()`.
- **FR-3:** Sidebar layout behavior is unchanged (Collections and History tabs).

## Non-functional requirements

- **NFR-1:** Minimal diff; no behavioral change.
- **NFR-2:** Existing tests pass; add or update tests if needed.

## Out of scope

- Refactoring other deferred imports elsewhere in the codebase.
- Changing sidebar tab labels, order, or splitter sizing.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `QTabWidget` imported at module level in `main_window.py` |
| AC-2 | No `QTabWidget` import inside `_build_layout()` |
| AC-3 | Sidebar still uses `QTabWidget` with Collections and History tabs |
| AC-4 | Affected unit tests pass |
