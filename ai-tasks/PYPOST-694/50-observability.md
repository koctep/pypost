# PYPOST-694: Observability

## New log events

| Event | Level | Location | Purpose |
| --- | --- | --- | --- |
| `history_manager_created id=%d` | INFO | `main.py` | Composition-root singleton identity at startup |
| `history_manager_source source=injected\|new` | DEBUG | `MainWindow.__init__` | Distinguish production injection vs test fallback |

## Unchanged

- `HistoryManager` internal DEBUG (`history_manager_saved`, load/save) unchanged.
- No new metrics counters — history metrics remain on append path.
