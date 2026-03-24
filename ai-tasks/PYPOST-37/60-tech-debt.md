# PYPOST-37: Technical Debt Analysis


## Shortcuts Taken

- **Search GUI tests skipped in CI** ([PYPOST-352](https://pypost.atlassian.net/browse/PYPOST-352)):
  `ResponseView` needs `QApplication` and a display; attempted tests crashed in headless CI.
  Manual testing covers this feature for now.
- **Search input without debounce** ([PYPOST-353](https://pypost.atlassian.net/browse/PYPOST-353)):
  Each keystroke scans the full document; acceptable for typical response sizes; debounce noted as
  optional follow-up.

## Code Quality Issues

- **Duplicate search nav logging** ([PYPOST-354](https://pypost.atlassian.net/browse/PYPOST-354)):
  `_find_next` and `_find_previous` repeat metrics/logging; a small helper (e.g.
  `_track_search_result()`) could deduplicate.
- **Hardcoded search UI strings** ([PYPOST-355](https://pypost.atlassian.net/browse/PYPOST-355)):
  Labels ("Previous", "Next", "Match case") and placeholder ("Search...") are inline; no i18n yet,
  acceptable for current scope.

## Missing Tests

- **ResponseView search untested** ([PYPOST-356](https://pypost.atlassian.net/browse/PYPOST-356)):
  Qt widget tests need `QApplication` and display (or Xvfb); project has no pytest-qt setup.
- No integration test for search flow (type, find next, match counter).
  — [PYPOST-357](https://pypost.atlassian.net/browse/PYPOST-357)

## Performance Concerns

- **Full-document match counting** ([PYPOST-358](https://pypost.atlassian.net/browse/PYPOST-358)):
  `_count_matches()` walks the whole document each time; large responses (100KB+) could feel slow;
  lazy count or an "N+ matches" cap were noted as mitigations.
- **Keystroke-driven full scans** ([PYPOST-359](https://pypost.atlassian.net/browse/PYPOST-359)):
  `_on_search_text_changed` runs per keystroke without debounce; fine for typical sizes.
- `_current_match_index()` caps iteration at 10000 to avoid infinite loops.
  — [PYPOST-360](https://pypost.atlassian.net/browse/PYPOST-360)

## Hardcoded Values

- `10000` in `_current_match_index` — safety limit for match iteration.
  — [PYPOST-361](https://pypost.atlassian.net/browse/PYPOST-361)
- UI strings: "Search...", "Previous", "Next", "Match case", "No matches".
  — [PYPOST-362](https://pypost.atlassian.net/browse/PYPOST-362)

## Follow-up Tasks

- **Debounce search input** ([PYPOST-363](https://pypost.atlassian.net/browse/PYPOST-363)):
  Add ~200–300 ms debounce on `_on_search_text_changed` if large responses feel laggy.
- Consider lazy match count or "N+ matches" cap for documents > 100KB.
  — [PYPOST-364](https://pypost.atlassian.net/browse/PYPOST-364)
- Add GUI tests if pytest-qt or xvfb is introduced to the project.
  — [PYPOST-365](https://pypost.atlassian.net/browse/PYPOST-365)
