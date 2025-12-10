# Architecture: PYPOST-18 - Variable Tooltips in Tables

## Research
To implement tooltips in `QTableWidget`, the following options were considered:

1.  **QTableWidget.setToolTip()**: Allows setting a static tooltip for the entire widget or individual cells.
    - *Pros*: Simplicity.
    - *Cons*: Static tooltip. If variables change, tooltips for all cells need to be updated. Does not allow dynamic reaction to variable changes without repainting the entire table.
2.  **Overriding `mouseMoveEvent`**:
    - *Pros*: Full control over display. Tooltip value can be calculated "on the fly" (lazy evaluation) using current variables.
    - *Cons*: Requires `setMouseTracking(True)` and manual `QToolTip` management.
3.  **Delegate (QStyledItemDelegate)**:
    - *Pros*: Custom rendering and editor can be customized.
    - *Cons*: Can intercept `helpEvent` (for tooltips) in delegate, but `mouseMoveEvent` logic at widget level seems more direct for global table behavior.

**Choice**: Overriding `mouseMoveEvent` (Option 2). This matches the approach already used in `VariableAwareLineEdit` and `VariableAwarePlainTextEdit` (PYPOST-16), ensuring codebase consistency.

## Implementation Plan

1.  **Modify `VariableHoverHelper`**:
    - Add `resolve_text(text, variables)` method for full variable substitution in a string. This is needed because a table cell might contain multiple variables or text with variables (e.g., `Bearer {{token}}`), and we want to show the final string.
2.  **Create `VariableAwareTableWidget`**:
    - New class in `pypost/ui/widgets/variable_aware_widgets.py`, inheriting from `QTableWidget`.
    - Implements `set_variables`, `mouseMoveEvent`, and `setMouseTracking(True)`.
3.  **Update `KeyValueTable`**:
    - Change inheritance in `pypost/ui/widgets/request_editor.py` from `QTableWidget` to `VariableAwareTableWidget`.
4.  **Integration into `RequestWidget`**:
    - In `set_variables` method, pass variables to `params_table` and `headers_table`.

## Architecture

### Changes in `pypost/ui/widgets/variable_aware_widgets.py`

Adding static method:
```python
@staticmethod
def resolve_text(text: str, variables: dict) -> str:
    # Replaces all occurrences of {{variable}} with their values.
```

New class:
```python
class VariableAwareTableWidget(QTableWidget, VariableHoverHelper):
    # ... implementation ...
```

### Changes in `pypost/ui/widgets/request_editor.py`

```python
class KeyValueTable(VariableAwareTableWidget):
    # Existing KeyValueTable logic remains unchanged,
    # variable functionality is inherited.
```

Update data flow:
`MainWindow` -> `RequestWidget.set_variables` -> `KeyValueTable.set_variables`.

## Q&A
- **Q**: Do we need to update tooltips if the table is not in focus?
- **A**: Tooltips are shown only on mouse hover. `mouseMoveEvent` fires when the mouse is over the widget. Data relevance is ensured by passing `variables` on environment change.
- **Q**: What about performance with a large number of rows?
- **A**: Tooltip calculation happens only for one cell under the cursor at the moment of hovering. This is a very cheap operation.
