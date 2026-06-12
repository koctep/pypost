# PYPOST-105: Unindent architecture

## Research

### Before

`_handle_closing_bracket` outdented only when `current_line_text.strip() == ""` — the whole line
had to be whitespace before inserting `}` or `]`.

### Desired behaviour

Outdent when **prefix** (text before cursor) and **suffix** (text after cursor) are both
whitespace-only, and leading spaces on the line are at least one `indent_size`. This matches
common editor smart-bracket behaviour and covers cursor-in-middle-of-whitespace lines.

## Implementation Plan

1. Add `_should_outdent_for_closing_bracket(line_text, column) -> bool`.
2. Add `_outdent_line_start(cursor)` — remove one indent level from line start; if the line remains
   whitespace-only, move cursor to end of line before inserting the bracket.
3. Call helpers from `_handle_closing_bracket` before `super().keyPressEvent(event)`.
4. Extend `tests/test_code_editor.py::TestCodeEditorKeyHandling`.

## Design decisions

| Decision | Rationale |
| --- | --- |
| Prefix/suffix whitespace check | Broader than whole-line check; avoids outdent when JSON content is present |
| Cursor to EOL after outdent on ws-only lines | Ensures `}` lands after remaining indent, not at column 0 |
| No logging changes | Pure UI keystroke handling; no new metrics |
