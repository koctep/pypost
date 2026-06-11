# PYPOST-431 Architecture — globalPosition() migration

## 1. Problem Summary

Qt 6 removed the implicit `QPoint` return from mouse events in favour of
`QPointF`-based `globalPosition()` / `position()`.  `QToolTip.showText` still
accepts `QPoint`, so the migration pattern is:

```python
# Before (deprecated)
event.globalPos()

# After (Qt 6)
event.globalPosition().toPoint()
```

## 2. Solution Overview

Surgical replacement at two call sites — no new helpers or abstractions.

### Files changed

| File | Location | Change |
|------|----------|--------|
| `pypost/ui/widgets/mixins.py` | `VariableHoverMixin._show_or_hide_tooltip` | `globalPos()` → `globalPosition().toPoint()` |
| `pypost/ui/widgets/variable_aware_widgets.py` | hover widgets + table | `globalPos()` / `pos()` → Qt 6 APIs |

## 3. Design Rationale

- **Single API surface**: Both sites already receive a `QMouseEvent`; no signature changes.
- **Integer coordinates**: `toPoint()` matches prior `globalPos()` semantics (integer
  screen coordinates for tooltip placement).
- **No version shim**: Project targets PySide6/Qt 6 only; no `hasattr` fallback needed.
- **Tests unchanged**: Test helpers already construct `QMouseEvent` with the modern
  constructor (`local_point`, `global_point`); production code change only.

## 4. Data Flow (unchanged)

```text
mouseMoveEvent(event)
  → _get_text_at_cursor(event) / itemAt(event.pos())
  → resolve expression / value
  → QToolTip.showText(global_position, value, widget)
```

Only the global-position extraction step changes.

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Sub-pixel rounding via `toPoint()` | Same as legacy `globalPos()`; acceptable for tooltips |
| Missed call sites | `rg globalPos pypost/` audit before close |
