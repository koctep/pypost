# PYPOST-132: Architecture — table hover performance

## PYPOST-122 coverage analysis

| Widget | Hover path | PYPOST-122 line-scoped scan |
| --- | --- | --- |
| `VariableAwarePlainTextEdit` | `VariableHoverMixin.mouseMoveEvent` | **Yes** — `_hover_line_scoped_scan` |
| `VariableAwareLineEdit` | `VariableHoverMixin.mouseMoveEvent` | N/A (single-line buffer) |
| `VariableAwareTableWidget` | Own `mouseMoveEvent` | **No** — separate code path |

Table hover already limits work to the cell under the cursor (`itemAt`). Cell text is
short (header names/values), so cost is O(cell length), not O(table size). The remaining
concern is **event frequency**: `mouseMoveEvent` fires often while the pointer stays in one
cell, repeating `resolve_text` unnecessarily.

## Chosen approach: per-cell resolution cache

Avoid debounce/throttle timers. Cache the last resolved value keyed by
`(row, column, cell_text)`:

```
mouseMoveEvent
  → itemAt
  → cache hit? show cached tooltip
  → EXPRESSION_PATTERN.search (fast bail-out for plain cells)
  → resolve_text (on miss)
  → store cache, show tooltip
```

Invalidate cache on `set_variables`, `set_hidden_keys`, and when the pointer leaves cells.

## Files

| File | Change |
| --- | --- |
| `pypost/ui/widgets/variable_aware_widgets.py` | `_hover_cache_*`, `_resolve_cell_hover`, cache invalidation |
| `tests/test_variable_hover.py` | Assert `resolve_text` called once for two moves on same cell |
| `doc/dev/ui_mixins.md` | Document table cache (not line-scoped scan) |

## Out of scope

- Character-index expression lookup within cells (cells are small; full `resolve_text` is fine
  on cache miss).
- Sharing cache logic with `VariableHoverMixin` (different input model).

## Test matrix

| Test | Covers |
| --- | --- |
| Existing `TestVariableAwareTableWidgetTooltips` | FR-1–FR-3 regression |
| New `test_repeated_mouse_move_reuses_hover_cache` | NFR-1 |
