# PYPOST-37: Technical Debt Analysis

## Shortcuts Taken

- No automated GUI tests for search: `ResponseView` requires `QApplication` and a display. Tests
  were attempted but crashed in headless CI. Manual testing is sufficient for this feature.
- No debounce for `_on_search_text_changed`: each keystroke triggers a full document scan. For
  typical response sizes this is acceptable; architecture noted debounce as optional mitigation.

## Code Quality Issues

- `_find_next` and `_find_previous` duplicate metrics/logging logic. Could be extracted into a
  helper (e.g. `_track_search_result()`), but duplication is minimal.
- Button labels ("Previous", "Next", "Match case") and placeholder ("Search...") are hardcoded.
  No i18n in the project; acceptable for current scope.

## Missing Tests

- No unit tests for `ResponseView` search logic. Qt widget tests require `QApplication` and a
  display (or headless Xvfb). The project has no pytest-qt or similar setup.
- No integration test for search flow (type, find next, match counter).

## Performance Concerns

- `_count_matches()` iterates the full document on every search. For large responses (e.g. 100KB+), this
  could be slow. Architecture noted "lazy count or N+ matches cap" as a mitigation.
- `_on_search_text_changed` runs on every keystroke. No debounce; rapid typing may cause multiple
  scans. Acceptable for typical response sizes.
- `_current_match_index()` has a safety limit of 10000 iterations to avoid infinite loops.

## Hardcoded Values

- `10000` in `_current_match_index` — safety limit for match iteration.
- UI strings: "Search...", "Previous", "Next", "Match case", "No matches".

## Follow-up Tasks

- Add debounce (e.g. 200–300 ms) to `_on_search_text_changed` if users report lag on large
  responses.
- Consider lazy match count or "N+ matches" cap for documents > 100KB.
- Add GUI tests if pytest-qt or xvfb is introduced to the project.
