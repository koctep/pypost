# Requirements: PYPOST-13 - Variable Tooltips

## Goals
Improve the experience of using environment variables by allowing the user to quickly view variable values without switching to the environment manager. Hovering over a variable placeholder (e.g., `{{baseUrl}}`) should display a tooltip with its current value.

## User Stories
- As a user, I want to see the value of the `{{baseUrl}}` variable when hovering over it in the address bar to ensure I am sending the request to the correct address.
- As a user, I want to see variable values in the request body (JSON body) to verify correct data substitution.
- As a user, I want tooltips to work for request headers and parameters.
- As a user, I want to see "Variable not found" or a similar message if the variable is not defined in the current environment.

## Acceptance Criteria
- [ ] **URL Input**: Hovering over `{{variable}}` in the URL bar displays a tooltip with the value.
- [ ] **Request Body**: Hovering over `{{variable}}` in the request body editor displays a tooltip with the value.
- [ ] **Headers/Params**: (Optional/Nice-to-have) Tooltips in header and parameter tables.
- [ ] **Dynamic Update**: When changing the environment, tooltips should show values from the new environment.
- [ ] **Missing Variable Handling**: If a variable is not found, an appropriate message is displayed (e.g., `<not defined>`).

## Task Description
Implement a mechanism to detect `{{name}}` variable tokens under the mouse cursor in various editing widgets.

### Technical Details
- **Language**: Python (PySide6).
- **Components**:
    - `RequestWidget`: must receive current environment variables from `MainWindow`.
    - `QLineEdit` (URL): Requires custom `mouseMoveEvent` handling and `fontMetrics` to determine text under cursor.
    - `QPlainTextEdit` (Body): Use `cursorForPosition` and `document().find()` or text analysis around cursor.
- **Integration**:
    - `MainWindow` must pass the variable dictionary to `RequestWidget` when the environment changes.
    - `RequestWidget` must propagate these variables to its child components (URL bar, Body editor).

## Q&A
- **Should syntax highlighting be shown for variables?**
    - This is useful, but the focus of this task is on tooltips. If it's easy to add (e.g., in Body via Highlighter) — good.
- **How to handle nested variables?**
    - Show only the first-level value (as `TemplateEngine.render` does for a single pass).
