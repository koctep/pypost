# PYPOST-250 Architecture — VariableHoverMixin typing

## 1. Problem Summary

`VariableHoverMixin` behaves as a QWidget extension but is typed as `object`. Two call
sites use `# type: ignore`:

- `super().mouseMoveEvent(event)`
- `QToolTip.showText(..., self, ...)`

## 2. Solution Overview

Adopt the standard **generic mixin** pattern:

```python
TWidget = TypeVar("TWidget", bound=QWidget)

class VariableHoverMixin(Generic[TWidget]):
    def mouseMoveEvent(self: TWidget, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
```

Consumers keep the same MRO (`VariableHoverMixin, QLineEdit`) without specifying
type parameters; checkers infer `TWidget` from the concrete widget base.

### Files changed

| File | Change |
|------|--------|
| `pypost/ui/widgets/mixins.py` | `Generic[TWidget]`, `QMouseEvent` hints, remove `type: ignore` |

No changes to `variable_aware_widgets.py` or tests (API unchanged).

## 3. Design Rationale

- **Generic bound to QWidget**: Documents the contract that hosts must be QWidget
  subclasses; enables `setMouseTracking` and `QToolTip.showText` without ignores.
- **Remove runtime `isinstance` guard**: With `bound=QWidget`, `setMouseTracking` is
  always valid on typed `self`; guard was only needed for untyped `object` self.
- **QMouseEvent import**: Typed `event` parameters on mixin methods.

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Mypy `super()` on mixin | `TWidget bound=QWidget` is the documented pattern; verify with tests |
| Breaking subclasses | Public method signatures unchanged |
