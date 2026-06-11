# PYPOST-363: Code Cleanup

## Lint and Format

- No new lint issues in `response_view.py` or `tests/test_response_view_search.py`.
- Imports ordered: `QTimer` added to existing `PySide6.QtCore` import.

## Review Notes

- `_schedule_search_text_changed` is a thin scheduler; search logic stays in
  `_on_search_text_changed`.
- Timer stopped before `clear_body` / `display_response` body mutations to avoid stale callbacks.
- `SEARCH_DEBOUNCE_MS` exported at module level for test timing (same pattern as threshold
  constants).

## Files Touched

| File | Change |
| --- | --- |
| `pypost/ui/widgets/response_view.py` | Debounce timer and scheduler |
| `tests/test_response_view_search.py` | Debounce behaviour tests |
| `doc/dev/response_search.md` | Debounce documentation |
