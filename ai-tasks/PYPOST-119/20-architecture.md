# PYPOST-119: Architecture — mouseMoveEvent hover performance review

## Coverage analysis

| Widget | Hover path | Mitigation |
| --- | --- | --- |
| `VariableAwarePlainTextEdit` | `VariableHoverMixin.mouseMoveEvent` | **PYPOST-122** — `_hover_line_scoped_scan` limits regex to current line |
| `VariableAwareLineEdit` | `VariableHoverMixin.mouseMoveEvent` | Single-line buffer; scan cost is O(URL length) |
| `VariableAwareTableWidget` | Own `mouseMoveEvent` | **PYPOST-132** — per-cell `(row, col, text)` resolution cache |

**Gap:** `VariableHoverMixin` still runs `find_expression_at_index` and `resolve_text` on every
`mouseMoveEvent` even when `scan_text` and `scan_index` are unchanged (common while the pointer
jitters over one token).

## Chosen approach: scan-position cache on mixin

Mirror the table strategy: cache the last lookup keyed by `(scan_text, scan_index)`:

```
mouseMoveEvent
  → _get_text_at_cursor
  → _prepare_hover_scan_context → (scan_text, scan_index)
  → cache hit? reuse expression + resolved value
  → find_expression_at_index (on miss)
  → resolve_text (on miss when expression found)
  → show/hide tooltip
```

Invalidate on `set_variables`, `set_hidden_keys`.

## Files

| File | Change |
| --- | --- |
| `pypost/ui/widgets/mixins.py` | `_hover_scan_cache_*`, `_resolve_hover_at_scan_index`, cache invalidation |
| `tests/test_variable_hover.py` | Repeated-move cache tests for line and body editors |
| `doc/dev/ui_mixins.md` | Document mixin scan cache alongside line-scoped and table caches |

## Out of scope

- Sharing cache implementation with `VariableAwareTableWidget` (different key model).
- Debounce/throttle timers.

## Test matrix

| Test | Covers |
| --- | --- |
| Existing `TestVariableAware*Tooltips` | FR-1–FR-3 regression |
| New `test_repeated_mouse_move_reuses_mixin_scan_cache` (line + body) | NFR-2 |
| Cache cleared on `set_variables` | NFR-3 |
