# Developer Documentation: PYPOST-250 — VariableHoverMixin typing

**Ticket**: PYPOST-250
**Date**: 2026-06-12

---

## 1. Overview

`VariableHoverMixin` now uses `Generic[TWidget bound=QWidget]` so static analyzers
treat `self` as the host widget. This removes `type: ignore` on `super().mouseMoveEvent`
and `QToolTip.showText`.

---

## 2. Documentation Updated

| File | Change |
|------|--------|
| `doc/dev/ui_mixins.md` | New guide for QWidget mixin typing pattern |
| `doc/dev/architecture.md` | Note generic mixin typing under UI widgets |

---

## 3. Maintainer Notes

When adding QWidget mixins:

- Use `TypeVar("T", bound=QWidget)` + `Generic[T]` and annotate `self: T` on methods.
- Do not inherit from `QWidget` in the mixin itself — keep mixin before the concrete
  widget in the MRO (`Mixin, QLineEdit`).
- Type mouse handlers with `QMouseEvent` from `PySide6.QtGui`.

---

## 4. Related

- `pypost/ui/widgets/mixins.py` — `VariableHoverMixin`
- `pypost/ui/widgets/variable_aware_widgets.py` — consumers
- `tests/test_variable_hover.py` — hover contract tests
