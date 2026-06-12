# PYPOST-97: Close debt — JsonHighlighter regex edge cases

**Issue type:** Debt
**Priority:** Medium
**Source:** `ai-tasks/PYPOST-11/40-tech-debt.md`
**Date:** 2026-06-12

---

## Goals

`JsonHighlighter` uses simple regular expressions for JSON token coloring. The patterns may
not cover every JSON spec edge case (multiline strings, unusual escapes, tricky key strings,
deep nesting). Decide whether to upgrade to a full parser or accept the limitation for
syntax coloring.

---

## User Stories

- As a **UI developer**, I want documented regex limitations on `JsonHighlighter`, so I
  know which miscoloring reports are expected vs. bugs.
- As a **reviewer**, I want dev docs to list known edge cases and the accepted trade-off,
  so follow-up tickets are not opened for intentional behavior.

---

## Definition of Done

1. Regex approach and known limitations documented on `JsonHighlighter` class docstring.
2. `doc/dev/json_syntax_highlighting.md` describes patterns and accepted edge cases.
3. Debt closed as accepted design for syntax coloring (no parser upgrade).
4. Existing `tests/test_json_highlighter.py` suite passes unchanged.

---

## Task Description

Accepted-debt closure from PYPOST-11. Regex rules are appropriate for `QSyntaxHighlighter`
block-by-block coloring where approximate token boundaries suffice for API JSON editing.

**Out of scope:** replacing regex with a JSON lexer, new highlight tests for every spec edge
case, or validation logic in the highlighter.
