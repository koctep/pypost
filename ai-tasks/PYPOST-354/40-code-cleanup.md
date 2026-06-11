# PYPOST-354: Code Cleanup

## Lint and Format

- No new lint issues in `response_view.py`.
- Helpers placed immediately before `_find_next` / `_find_previous` for locality.

## Review Notes

- `_search_text_or_clear` returns `None` for empty query (same clear-and-return semantics).
- `_track_search_result` assumes find already ran; callers own `body_view.find` direction.
- Typed-search path in `_on_search_text_changed` intentionally unchanged.

## Files Touched

| File | Change |
| --- | --- |
| `pypost/ui/widgets/response_view.py` | Extract navigation helpers |
| `doc/dev/response_search.md` | Document helpers |
