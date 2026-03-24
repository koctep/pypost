# PYPOST-12: Technical Debt Analysis


## Shortcuts Taken

- **No Tests**: Creation of automated tests was skipped by user request. Auto-indentation and paste logic is not covered by tests. — [PYPOST-104](https://pypost.atlassian.net/browse/PYPOST-104)
- **Simplified Unindent Logic**: Unindentation works only if the line contains *only* the closing bracket and spaces before it. In more complex cases (e.g., code on the same line), unindentation might not work or work unexpectedly. — [PYPOST-105](https://pypost.atlassian.net/browse/PYPOST-105)
- **Manual Font Propagation**: In `MainWindow.apply_settings`, the font is manually applied to individual widgets (`collections_view`, `tabs`, `menuBar`, etc.) because automatic inheritance from `QApplication` did not work for all elements. This creates a risk of missing new elements when expanding UI. — [PYPOST-106](https://pypost.atlassian.net/browse/PYPOST-106)

## Code Quality Issues

- **Manual Font Propagation**: (See above). This violates DRY principle and complicates UI maintenance. — [PYPOST-107](https://pypost.atlassian.net/browse/PYPOST-107)

## Missing Tests

- **CodeEditor tests** ([PYPOST-108](https://pypost.atlassian.net/browse/PYPOST-108)):
  - `update_indent_size` and `reformat_text`.

## Performance Concerns

- **JSON Parsing on Paste**: When pasting *very* large text, attempting to parse it as JSON might cause interface lag. Currently, this is executed in the main UI thread. — [PYPOST-109](https://pypost.atlassian.net/browse/PYPOST-109)

## Follow-up Tasks

- Create tests for `CodeEditor`. — [PYPOST-110](https://pypost.atlassian.net/browse/PYPOST-110)
- Implement asynchronous JSON check on paste for large data volumes (optional). — [PYPOST-111](https://pypost.atlassian.net/browse/PYPOST-111)
- Investigate reasons for font inheritance issues and refactor `apply_settings` for a cleaner solution (possibly via global QSS). — [PYPOST-112](https://pypost.atlassian.net/browse/PYPOST-112)
