# Body Editor Auto-Indent and Bracket Outdent

## Overview

The request Body tab uses `CodeEditor` (`pypost/ui/widgets/code_editor.py`) for JSON/YAML editing.
Enter and closing-bracket keys adjust indentation to match common editor expectations.

## Enter key

When the user presses Enter:

1. The new line copies leading whitespace from the current line.
2. If the trimmed current line ends with `{` or `[`, one extra `indent_size` spaces are appended.

## Closing `}` or `]`

When the user types `}` or `]`:

1. Let `prefix` be text before the cursor and `suffix` text after the cursor on the current line.
2. If both `prefix` and `suffix` are whitespace-only and the line has at least `indent_size`
   leading spaces, remove one indent level from the **start** of the line.
3. If the line is still whitespace-only, move the cursor to the end of that whitespace before
   inserting the bracket (so mid-line whitespace cursors still produce `  }` not `}  `).
4. Insert the typed bracket via the default `keyPressEvent` handler.

Non-whitespace content before or after the cursor disables auto-outdent — the bracket is inserted
at the cursor without changing line-leading spaces.

## Configuration

Indent width comes from application settings (`indent_size`, default 2) via
`CodeEditor.update_indent_size`.

## Tests

See `tests/test_code_editor.py::TestCodeEditorKeyHandling` (PYPOST-104, PYPOST-105).
