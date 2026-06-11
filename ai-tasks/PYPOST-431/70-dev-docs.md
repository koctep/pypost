# Developer Documentation: PYPOST-431 — Qt 6 mouse event coordinates

**Ticket**: PYPOST-431
**Date**: 2026-06-11

---

## 1. Overview

Variable-hover tooltips now use the Qt 6 coordinate API.  This removes
`DeprecationWarning` noise from pytest without changing tooltip behaviour.

---

## 2. Documentation Updated

| File | Change |
|------|--------|
| `doc/dev/tech-debt/PYPOST-431.md` | Closure note; resolved `globalPos` item from PYPOST-434 |

---

## 3. Maintainer Notes

When touching mouse-event handlers in UI widgets:

- Prefer `event.globalPosition().toPoint()` over `event.globalPos()`.
- Prefer `event.position().toPoint()` over `event.pos()`.
- `QToolTip.showText` expects integer `QPoint` screen coordinates.

---

## 4. Related

- `pypost/ui/widgets/mixins.py` — `VariableHoverMixin`
- `tests/test_variable_hover.py` — hover contract tests
