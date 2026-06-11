# PYPOST-364: Technical Debt Analysis

## Shortcuts Taken

- **Character count vs byte size:** Threshold uses `len(toPlainText())` (UTF-16 code units in Qt)
  rather than HTTP response byte size. Close enough for the 100KB UX goal; edge case for multibyte
  text only.

## Code Quality Issues

- None introduced. Constants `LARGE_DOC_CHAR_THRESHOLD` and `MATCH_COUNT_CAP` are module-level and
  documented in dev docs.

## Missing Tests

- No test for capped display when `current == 0` (cursor not on a match) — rare after typed
  search which moves to first match.

## Performance Concerns

- **Large doc, few matches:** Still requires a full scan when match count stays under the cap.
  Acceptable; cap addresses match-heavy documents.
- **Keystroke debounce:** Remains out of scope ([PYPOST-363](https://pypost.atlassian.net/browse/PYPOST-363)).

## Hardcoded Values

- `100 * 1024` — large document threshold.
- `1000` — match count cap for large documents.
- `10000` — pre-existing safety limit in `_current_match_index()`.

## Follow-ups

- None required for task closure.
