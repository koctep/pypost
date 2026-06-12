# PYPOST-114: Variable tooltip styling — QSS customization hook

## Goals

Variable hover tooltips (from PYPOST-13) use Qt's native `QToolTip.showText` API. There was
no documented or configurable styling path; appearance followed the platform default. Users
and theme authors need a single, maintainable way to adjust tooltip colors without editing
Python code.

## User Stories

- As a pypost user, I want variable hover tooltips to match the application theme so they
  feel consistent with menus and other styled controls.
- As a theme author, I want to customize tooltip appearance via QSS so I do not need to
  change widget code.

## Definition of Done

| ID | Criterion |
|----|-----------|
| AC-1 | `main.qss` exposes a `QToolTip` rule using palette roles (no hardcoded hex in Python) |
| AC-2 | Developer docs describe how variable hover tooltips pick up global QSS |
| AC-3 | A test asserts loaded styles include the tooltip QSS hook |
| AC-4 | Existing variable hover tests pass unchanged |

## Scope

**In scope:** QSS hook in bundled stylesheet, documentation, StyleManager test.

**Out of scope:** Per-widget tooltip themes, custom tooltip widgets, appearance UI tests.

## Constraints

- No behavioural change to tooltip text or show/hide logic.
- Follow existing `StyleManager` / `main.qss` patterns (palette roles, bundled `.qss` files).

## Programming language

Python (tests); QSS for styling.
