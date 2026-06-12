# PYPOST-105: Broaden unindent logic in body editor

Related debt: [PYPOST-12](https://pypost.atlassian.net/browse/PYPOST-12)

## Goals

When users type a closing `}` or `]` in the request Body `CodeEditor`, indentation should decrease
predictably whenever they are closing a block on a whitespace-only portion of the line — not only
when the entire line was empty before the keystroke.

## User Stories

- As a **user**, I want typing `}` or `]` on an over-indented whitespace line to outdent by one
  indent level before inserting the bracket, even when my cursor is not at the end of the line.
- As a **user**, I want closing brackets typed after real JSON content on the same line to stay
  inline without unexpected outdent.

## Definition of Done

- [x] Outdent triggers when only whitespace surrounds the cursor on the current line.
- [x] Outdent does not run when non-whitespace content appears before or after the cursor.
- [x] `}` and `]` share the same behaviour.
- [x] Unit tests cover whitespace-only, mid-whitespace cursor, square bracket, and content guard.
- [x] Developer documentation describes the rule.

## Task Description

PYPOST-12 shipped simplified unindent logic that checked `line.strip() == ""`. That missed cases
where trailing whitespace or cursor position differed while the user still intended a block close.
This task broadens the condition and fixes cursor placement after outdent.
