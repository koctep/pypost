# PYPOST-15: Technical Debt Analysis

## Shortcuts Taken

- **No Tests**: Creation of automated tests was skipped by user request. Auto-indentation and paste logic is not covered by tests.
- **Simplified Unindent Logic**: Unindentation works only if the line contains *only* the closing bracket and spaces before it. In more complex cases (e.g., code on the same line), unindentation might not work or work unexpectedly.
- **Manual Font Propagation**: In `MainWindow.apply_settings`, the font is manually applied to individual widgets (`collections_view`, `tabs`, `menuBar`, etc.) because automatic inheritance from `QApplication` did not work for all elements. This creates a risk of missing new elements when expanding UI.

## Code Quality Issues

- **Manual Font Propagation**: (See above). This violates DRY principle and complicates UI maintenance.

## Missing Tests

- Tests for `CodeEditor`:
    - `update_indent_size` and `reformat_text`.

## Performance Concerns

- **JSON Parsing on Paste**: When pasting *very* large text, attempting to parse it as JSON might cause interface lag. Currently, this is executed in the main UI thread.

## Follow-up Tasks

- Create tests for `CodeEditor`.
- Implement asynchronous JSON check on paste for large data volumes (optional).
- Investigate reasons for font inheritance issues and refactor `apply_settings` for a cleaner solution (possibly via global QSS).
