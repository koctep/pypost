# Architecture: PYPOST-15 - Auto-indentation and JSON Auto-formatting

## Research

### PySide6 QPlainTextEdit Event Overriding

To implement auto-indentation and paste handling, it is necessary to override event methods in a class inheriting `QPlainTextEdit`:

*   Intercept `Qt.Key_Return` (or `Qt.Key_Enter`) press.
*   Analyze text before cursor to determine indentation.
*   Implement logic for increasing/preserving indentation.
*   Intercept `}` or `]` press to decrease indentation (might require `textChanged` processing or input filtering, but `keyPressEvent` is simpler for start).

*   This is the standard method for handling Paste in Qt widgets.
*   Text can be obtained from `source.text()`.
*   Try to parse as JSON.
*   If valid JSON -> format (`json.dumps(data, indent=4)`) and insert.
*   If not -> call `super().insertFromMimeData(source)` (standard paste).

### Architectural Patterns

*   **Inheritance**: Creating a specialized widget `CodeEditor` (or `JsonEditor`) inheriting `QPlainTextEdit`.
*   **Composition**: `RequestWidget` will use `CodeEditor` instead of `QPlainTextEdit`.
*   **Separation of Concerns**: Formatting and input handling logic is encapsulated in `CodeEditor`, not cluttering `RequestWidget`.

## Implementation Plan

1.  Create `CodeEditor` class in `pypost/ui/widgets/code_editor.py`.
2.  Implement `keyPressEvent` method to handle `Enter` (indentation calculation).
3.  Implement `insertFromMimeData` method to intercept paste and auto-format.
4.  Replace `QPlainTextEdit` with `CodeEditor` in `pypost/ui/widgets/request_editor.py`.
5.  Test manual entry and paste.

## Architecture

### Class Diagram
[Diagram]

### Modules

*   **Class `CodeEditor`**:
    *   Inherits from `QPlainTextEdit`.
    *   **Responsibility**: Provide a convenient interface for editing code (JSON) with support for auto-indentation and formatting.
    *   **Methods**:
        *   `keyPressEvent`: "Smart" Enter logic.
        *   `insertFromMimeData`: "Smart" paste logic.

*   **Class `RequestWidget`**:
    *   Existing class.
    *   **Change**: Replace `self.body_edit = QPlainTextEdit()` with `self.body_edit = CodeEditor()`.
    *   Connection of `JsonHighlighter` to the new editor remains unchanged (it works with `QTextDocument`, which both have).

## Q&A

*   **How to handle `Tab`?**
    *   By default, `QPlainTextEdit` inserts a tab character. We can override to insert 4 spaces, but requirements don't explicitly state this. Leave standard behavior or 4 spaces (Python/JSON standard). *Decision: use 4 spaces for consistency.*
*   **Is a separate file needed for CodeEditor?**
    *   Yes, better to move to a separate file `code_editor.py` for reuse and code cleanliness.
