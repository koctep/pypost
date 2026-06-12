# PYPOST-101: Guard JsonHighlighter regex cost on large blocks

## Goals

Users viewing or editing very large JSON responses (for example minified megabyte payloads on
a single line) must not experience noticeable UI freezes caused by syntax-highlighting regex
scans on oversized document blocks.

## User Stories

- As a user, I want the response viewer to remain responsive when displaying huge JSON bodies,
  even if full syntax coloring is not applied to every character.
- As a user, I want normal-sized JSON (typical API request/response bodies) to keep the
  existing syntax highlighting behavior.

## Definition of Done

1. `JsonHighlighter` skips expensive regex highlighting when a single `QTextDocument` block
   exceeds a documented character threshold.
2. Blocks at or below the threshold continue to receive full JSON and placeholder coloring.
3. Automated tests cover the skip path and a boundary case near the threshold.
4. Developer documentation describes the limit and rationale.

## Task Description

Address performance debt from PYPOST-11: `QSyntaxHighlighter` runs per block, but minified JSON
can place an entire payload in one block. Complex string/key regexes on multi-megabyte lines
can stall the UI thread. Introduce a safe upper bound with an early return rather than
blocking the event loop.

## Scope

- `pypost/ui/widgets/json_highlighter.py`
- `tests/test_json_highlighter.py`
- `doc/dev/json_syntax_highlighting.md`

Out of scope: incremental JSON lexer, async highlighting, or user-configurable threshold UI.
