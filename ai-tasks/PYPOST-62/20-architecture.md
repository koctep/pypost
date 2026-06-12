# PYPOST-62: Architecture — history entry index

## Scope

`HistoryPanel` in `pypost/ui/widgets/history_panel.py` only.

## Data structures

- Keep `self._entries: List[HistoryEntry]` for ordered iteration in `_apply_filter`.
- Add `self._entries_by_id: Dict[str, HistoryEntry]` for O(1) lookup by `entry.id`.

## Lifecycle

1. `refresh()` loads entries from `HistoryManager.get_entries()`.
2. Immediately rebuild `_entries_by_id = {entry.id: entry for entry in self._entries}`.
3. `_apply_filter()` unchanged — list items still store `entry.id` in `Qt.UserRole`.

## Lookup

`_selected_entry()`:

- Read `entry_id` from `currentItem().data(Qt.UserRole)`.
- Return `self._entries_by_id.get(entry_id)` (None if missing or no selection).

## Testing

- `tests/test_history_panel.py`: select non-first row; assert correct entry; call
  `refresh()` with a smaller entry set and assert index reflects new data.

## Observability

No new log events. Existing `history_panel_refreshed` debug log remains sufficient.
