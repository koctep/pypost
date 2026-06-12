# PYPOST-62: Dev Docs

## Updated

No `doc/dev/` changes required. The index is a private implementation detail of
`HistoryPanel`; public behaviour and signals are unchanged.

## Key points for developers

1. `_entries_by_id` must be rebuilt whenever `_entries` is replaced (currently only in
   `refresh()`).
2. List widget items continue to store `entry.id` in `Qt.UserRole` for selection lookup.
