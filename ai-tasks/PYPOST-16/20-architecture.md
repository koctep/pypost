# Architecture: PYPOST-16 - Variable Tooltips

## Research

To implement tooltips when hovering over `{{variable}}` variables, the following approaches in PySide6/Qt were considered:

1.  **Standard Tooltip (`setToolTip`)**:
    -   Standard `setToolTip` sets static text for the entire widget.
    -   For dynamic content, `event` or `mouseMoveEvent` needs to be overridden.

2.  **`QLineEdit` (URL Bar)**:
    -   Using `fontMetrics` and cursor position (`cursorPositionAt`) allows determining the character under the mouse.
    -   Need to find boundaries of the `{{...}}` token around the character under the cursor.
    -   To display the tooltip, `QToolTip.showText(global_pos, value, widget)` can be used.

3.  **`QPlainTextEdit` (Body Editor)**:
    -   Has `cursorForPosition(pos)` method which returns `QTextCursor` for a given pixel position.
    -   Can get text block and analyze word under cursor.
    -   Similarly, need to search for `{{...}}` pattern.
    -   Overriding `mouseMoveEvent` requires enabling `setMouseTracking(True)`.

## Implementation Plan

1.  **Extend `RequestWidget` Interface**:
    -   Add `set_variables(variables: dict)` method.
    -   Store variables in `self.variables` attribute.

2.  **Update `MainWindow`**:
    -   On environment change (`on_env_changed`), call `set_variables` for the active (or all) `RequestWidget`.

3.  **Create `VariableHoverMixin`**:
    -   To avoid code duplication for variable search logic.
    -   Methods:
        -   `find_variable_at_index(text, index)`: Returns variable name or None.
        -   `get_variable_value(name)`: Returns value from stored dictionary.

4.  **Customize `QLineEdit` (UrlInput)**:
    -   Create `VariableAwareLineEdit(QLineEdit)` class.
    -   Enable `setMouseTracking(True)`.
    -   Override `mouseMoveEvent`.
    -   Logic: get cursor position -> find token -> if token == variable -> show tooltip.

5.  **Customize `QPlainTextEdit` (BodyEditor)**:
    -   Create `VariableAwarePlainTextEdit(QPlainTextEdit)` class.
    -   Enable `setMouseTracking(True)`.
    -   Override `mouseMoveEvent`.
    -   Use `cursorForPosition` to determine position in text.

## Architecture

### New Classes

*   `VariableHoverHelper`: Helper class/mixin containing logic for finding variables in string by index.
    ```python
    class VariableHoverHelper:
        def find_variable_at_index(self, text: str, index: int) -> str | None:
            # Logic to find {{name}} around index
            pass
    ```

*   `VariableAwareLineEdit(QLineEdit, VariableHoverHelper)`
*   `VariableAwarePlainTextEdit(QPlainTextEdit, VariableHoverHelper)`

### Changes in Existing Classes

*   `RequestWidget`:
    -   Replace `QLineEdit` with `VariableAwareLineEdit`.
    -   Replace `QPlainTextEdit` (for Body) with `VariableAwarePlainTextEdit`.
    -   Add `set_variables(variables)` method.
    -   Pass variables to child widgets during initialization and update.

*   `MainWindow`:
    -   In `on_env_changed`, get variables and update current tab (and other open ones).
    -   In `on_tab_changed` (if needed), update variables for new tab (though they should already be updated on env change).

## Q&A

-   **How to handle nested variables?**
    -   Show value "as is" in dictionary. If value itself contains a variable, can (optionally) try to resolve it too, but direct mapping is enough for first version.
-   **`mouseMoveEvent` performance?**
    -   Event fires frequently. Checks must be fast. Show tooltip only if value changed or if we entered variable zone.
