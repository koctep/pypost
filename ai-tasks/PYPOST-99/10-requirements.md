# PYPOST-99: Replace hardcoded JsonHighlighter colors

## Context

- **Jira:** PYPOST-99
- **Origin:** [PYPOST-11](https://pypost.atlassian.net/browse/PYPOST-11)
  (`40-tech-debt.md`): JsonHighlighter colors were hardcoded in the widget class.
- **Related:** [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398) — theme extraction;
  [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395) — dark palette and resolver.

## Problem statement

JSON syntax colors (keywords, numbers, strings, keys, template placeholders) were embedded
directly in `JsonHighlighter`. Theme changes or dark-mode support required editing the
highlighter instead of a single theme definition.

## Goals

- Centralize JSON syntax highlight colors in an application theme module.
- Preserve default light-theme appearance (no visual regression).
- Enable dark-theme and runtime palette switching without duplicating literals in the
  highlighter.

## Scope

### In scope

- Verify colors live in `pypost/ui/theme/json_syntax_theme.py` (`JsonSyntaxColors`).
- Verify `JsonHighlighter` reads colors from theme via optional `colors` and
  `resolve_json_syntax_colors()`.
- Verify unit tests cover defaults, custom injection, and `set_colors`.
- Close PYPOST-11 hardcoded-colors debt item.

### Out of scope

- Settings UI for user-editable colors.
- Changing regex rules or highlight behavior.

## Functional requirements

1. **FR-1:** Default colors match legacy values (darkblue, blue, green, purple, darkorange).
2. **FR-2:** `JsonHighlighter` accepts optional `colors`; when omitted, resolver applies.
3. **FR-3:** `RequestEditor` and `ResponseView` wiring works without mandatory call-site
   changes.
4. **FR-4:** Tests verify default, custom, dark palette, and `set_colors` rebinding.

## Acceptance criteria

1. **AC-1:** No color string literals in `json_highlighter.py` rule setup.
2. **AC-2:** All `test_json_highlighter.py` cases pass.
3. **AC-3:** Theme module documents light and dark palettes plus resolver.
4. **AC-4:** `doc/dev/json_syntax_highlighting.md` documents theme location and usage.

## Programming language

**Python** — PySide6, dataclasses, pytest + unittest, offscreen Qt platform.
