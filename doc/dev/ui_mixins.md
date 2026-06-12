# UI widget mixins

## VariableHoverMixin

`pypost/ui/widgets/mixins.py` defines `VariableHoverMixin`, shared tooltip logic for
`{{variable}}` placeholders in text widgets.

### Typing pattern (PYPOST-250)

The mixin uses a generic bound to `QWidget` so type checkers understand `self`:

```python
TWidget = TypeVar("TWidget", bound=QWidget)

class VariableHoverMixin(Generic[TWidget]):
    def mouseMoveEvent(self: TWidget, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
```

Consumers declare multiple inheritance without type parameters:

```python
class VariableAwareLineEdit(VariableHoverMixin, QLineEdit):
    ...
```

Checkers infer `TWidget` as `QLineEdit` from the MRO.

### Requirements for host widgets

- Host must be a `QWidget` subclass (typically `QLineEdit` or `QPlainTextEdit`).
- Host must implement `_get_text_at_cursor(event) -> tuple[str, int]`.
- Initialize the mixin after the QWidget base: `QLineEdit.__init__(self)` then
  `VariableHoverMixin.__init__(self)`.

### Related

- Variable-aware widgets: `pypost/ui/widgets/variable_aware_widgets.py`
- Tests: `tests/test_variable_hover.py`
