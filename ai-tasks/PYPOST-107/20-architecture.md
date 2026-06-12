# PYPOST-107: Body editor font architecture

## Research

### Current state (before)

- Global font: `StyleManager.apply_styles(app, font_size=N)` + `app.setFont` (PYPOST-106).
- `TabsPresenter.apply_settings` loops tabs for indent reformat and JSON colors; docstring
  mentioned "font" but no `setFont` on `body_edit`.
- `CodeEditor.update_indent_size` recalculated tab stops from `document().defaultFont()` only
  when indent width changed, not when font size changed.

### Gap

After Settings changes font size, inherited editor font updates via QSS but tab-stop distance
and line-number gutter width stayed sized for the old font metrics.

## Implementation Plan

1. Extract `_refresh_font_metrics()` in `CodeEditor` — tab stops + gutter width from current
   document font and `indent_size`.
2. Call from `update_indent_size` and `changeEvent` when `event.type() == FontChange`.
3. Clarify `TabsPresenter.apply_settings` docstring (indent/colors only).

## Design decisions

| Decision | Rationale |
| --- | --- |
| `changeEvent` not presenter loop | DRY — any font source (settings, theme, parent) triggers refresh |
| Reuse indent path for metrics | Single method for tab stops and gutter |
| No `setFont` in presenter | Global theme is sole font-size authority |

## Risks

- **Monospace override widgets**: out of scope (MCP preview uses local monospace hint).
