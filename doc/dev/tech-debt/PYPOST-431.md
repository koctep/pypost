# Technical Debt — PYPOST-431 (Qt mouse event API)

## Resolved

`QMouseEvent.globalPos()` in variable-hover tooltip paths was migrated to
`globalPosition().toPoint()` in:

- `pypost/ui/widgets/mixins.py` (`VariableHoverMixin`)
- `pypost/ui/widgets/variable_aware_widgets.py` (`VariableAwareTableWidget`)

This closes the item noted in `doc/dev/tech-debt/PYPOST-434.md` §2.

## Also migrated (same ticket)

`event.pos()` → `event.position().toPoint()` in `variable_aware_widgets.py` hover
paths so `tests/test_variable_hover.py` runs clean under `-W error::DeprecationWarning`.
