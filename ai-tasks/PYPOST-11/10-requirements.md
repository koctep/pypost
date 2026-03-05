# Requirements: PYPOST-11 - JSON Syntax Highlighting

## Goals
Improve visual perception of JSON data in the request editor and response viewer by adding syntax highlighting. This will simplify reading and editing JSON structures.

## User Stories
- As a user, I want to see highlighted JSON syntax in the request body input field (Body) to easily distinguish keys, values, and data structure.
- As a user, I want to see highlighted JSON syntax in the response viewer field to quickly find the necessary information in the server response.

## Acceptance Criteria
- [ ] `JsonHighlighter` class implemented (based on `QSyntaxHighlighter`).
- [ ] Highlighting applied to request body input field (`QPlainTextEdit`) in `RequestWidget`.
- [ ] Highlighting applied to response viewer field (`QTextEdit` or `QPlainTextEdit`) in `ResponseView`.
- [ ] Main JSON elements are highlighted:
    - Keys (strings in dictionary keys).
    - String values.
    - Numbers.
    - Literals (`true`, `false`, `null`).
- [ ] Highlighting works correctly when editing text (in request).

## Task Description
Develop a JSON syntax highlighting component for use in PySide6 text fields.
The component must recognize JSON structure and color elements in different colors.

### Components to Change
1. **New File**: `pypost/ui/widgets/json_highlighter.py` - `QSyntaxHighlighter` implementation.
2. `pypost/ui/widgets/request_editor.py` - connect highlighter to `self.body_edit`.
3. `pypost/ui/widgets/response_view.py` - connect highlighter to `self.body_view`.

### Color Scheme (approximate)
- **Keys**: Dark Blue / Purple.
- **Strings**: Green / Dark Green.
- **Numbers**: Blue / Orange.
- **Literals (true/false/null)**: Bold Blue / Red.

## Q&A
- **Is dark theme support needed?**
    - For now, use fixed colors that read well on a light background (current default theme). If a dark theme is introduced, colors will need to be moved to style settings, but that is out of scope for this task.
- **What if JSON is invalid?**
    - The highlighter usually works based on regular expressions or lexical analysis, so it will highlight what looks like JSON elements, even if the overall structure is broken. This is acceptable behavior.
