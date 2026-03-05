# Requirements: PYPOST-12 - Auto-indentation and JSON Auto-formatting

## Goals
Improve the convenience of editing JSON in the "Body" field of the request editor by automating formatting. This will allow users to write and paste JSON code faster while maintaining its readability.

## User Stories
- As a user, I want new lines to automatically receive the correct indentation when I press Enter in the JSON editor, so I don't have to press Tab manually.
- As a user, I want the indentation to increase after an opening bracket `{` or `[` when pressing Enter, so the JSON structure is visually clear.
- As a user, I want the indentation to automatically decrease when entering a closing bracket `}` or `]`, matching the nesting level of the block.
- As a user, I want unformatted JSON text to be automatically formatted (pretty-print) upon pasting, so I can immediately see the data structure.

## Acceptance Criteria
- [ ] Code editor component implemented (e.g., `CodeEditor` or `QPlainTextEdit` extension).
- [ ] **Auto-indentation**:
    - When pressing `Enter`, the new line preserves the indentation of the previous line.
    - If the line ends with `{` or `[`, the indentation of the next line increases (by 4 spaces).
    - When entering a closing bracket `}` or `]`, the indentation decreases.
- [ ] **Format on Paste**:
    - When pasting text, if it is valid JSON, it is formatted with indentation (indent=4).
    - If the text is invalid JSON, it is inserted as is.
- [ ] New component integrated into `RequestWidget` instead of standard `QPlainTextEdit` for Body field.

## Task Description
Create a specialized text editor widget (inheriting from `QPlainTextEdit`) that will handle keyboard and paste events to ensure convenient JSON editing.

### Technical Details
- Implementation Language: **Python** (PySide6).
- Base Class: `QPlainTextEdit`.
- Indentation: 4 spaces.

### Main Scenarios

1. **Text Entry**:
   ```
   {
       "key": "value"
       | <-- cursor should be here (with indentation)
   ```

2. **Nested Structure Entry**:
   ```
   {
       "key": {
           | <-- cursor here (increased indentation)
   ```

3. **Paste**:
   - In buffer: `{"a":1,"b":2}`
   - Action: Paste
   - Result in editor:
     ```json
     {
         "a": 1,
         "b": 2
     }
     ```

## Q&A
- **Do we need to format existing text via button?**
    - In the scope of this task - no, only on paste. On-demand formatting can be added as a separate task if needed.
- **What if JSON is very large?**
    - Auto-formatting should work reasonably fast. For very large files (megabytes), `json.dumps` might be slow, but for typical HTTP requests, this is not a problem.
