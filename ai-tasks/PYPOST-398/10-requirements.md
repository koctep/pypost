# PYPOST-398: Move JsonHighlighter colors to application theme

## Context

- **Jira:** PYPOST-398
- **Origin:** Follow-up from [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9)
  (`40-tech-debt.md`): JsonHighlighter colors were hardcoded in the widget class.
- **Related:** [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395) — dark-theme
  palette (future).

## Problem statement

JSON syntax colors (keywords, numbers, strings, keys, template placeholders) are embedded
directly in `JsonHighlighter`. Any theme change or dark-mode support requires editing the
highlighter instead of adjusting a single theme definition.

## Goals

- Centralize JSON syntax highlight colors in an application theme module.
- Preserve current default appearance for users (no visual regression).
- Enable future theme variants (e.g. dark mode in PYPOST-395) without duplicating color
  literals in the highlighter.

## Scope

### In scope

- Extract color definitions from `JsonHighlighter` into a theme/config type with defaults.
- Wire `JsonHighlighter` to read colors from that type.
- Unit test that custom colors are applied when supplied.
- Developer documentation for the theme API.

### Out of scope

- Settings UI for user-editable colors.
- Dark-theme palette implementation ([PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)).
- Changing regex rules or highlight behavior.
- Persisting colors in `settings.json`.

## User stories

- As a **developer**, I want JSON highlight colors defined in one place so I can add a dark
  theme without touching highlighter logic.
- As a **user**, I want JSON in request/response editors to look the same as before this
  change.

## Functional requirements

1. **FR-1:** Default colors match pre-refactor values (darkblue, blue, green, purple,
   darkorange).
2. **FR-2:** `JsonHighlighter` accepts an optional colors object; when omitted, defaults
   apply.
3. **FR-3:** Existing `RequestEditor` and `ResponseView` wiring continues to work without
   mandatory call-site changes.
4. **FR-4:** Tests verify default and custom color injection.

## Acceptance criteria

1. **AC-1:** No color string literals remain in `json_highlighter.py` rule setup.
2. **AC-2:** All existing `test_json_highlighter.py` cases pass unchanged.
3. **AC-3:** At least one test proves a non-default color is applied via the theme object.
4. **AC-4:** `doc/dev/json_syntax_highlighting.md` documents theme location and usage.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | Light-theme defaults remain the product baseline until PYPOST-395. |
| **Assumption** | Named Qt colors (`QColor("darkblue")`) remain valid for defaults. |
| **Risk** | Low: refactor-only; behavior preserved via default theme. |

## Programming language

**Python** — PySide6, dataclasses, pytest + unittest, offscreen Qt platform.
