# Response Body Search

## Overview

The response view supports plain-text search within the HTTP response body. Users can quickly find
specific values in large JSON or text payloads without manual scrolling.

Features:
- Search input with placeholder "Search..."
- Previous/Next navigation between matches
- Match case option (case-sensitive search)
- Match counter (e.g. "2 of 5" or "No matches")
- Ctrl+F to focus search input
- Enter to find next match

## Architecture

- **`ResponseView` (`pypost/ui/widgets/response_view.py`)**:
  - Search bar is merged with the status bar (Status, Time, Size) in one row.
  - Uses `QTextEdit.find()` with `QTextDocument.FindFlag` for search.
  - Search logic is self-contained; no changes to `MainWindow` or `RequestTab`.
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Tracks search actions: `gui_response_search_actions_total{source, has_matches}`

## API / Usage

### `ResponseView._find_next(source: str = "next")`

Finds the next occurrence of the search text from the current cursor position.

- **source**: "next" (button), "enter" (Return key), or "typed" (text change)
- Updates match counter and emits metrics.

### `ResponseView._find_previous(source: str = "previous")`

Finds the previous occurrence using `FindBackward` flag.

### `ResponseView._count_matches() -> int`

Counts total matches in the document. Restores cursor after counting.

### `ResponseView._current_match_index() -> int`

Returns the 1-based index of the match containing the current cursor, or 0 if not on a match.

### `ResponseView._update_match_count() -> int`

Updates the status label ("N of M", "No matches", or "N match(es)"). Returns total match count.

### `ResponseView._on_search_text_changed()`

Triggered when the user types or clears the search input. Moves cursor to start, finds first match,
and updates the counter.

## Configuration

No configuration. Search is cleared automatically when:
- `clear_body()` is called
- `display_response()` is called (new response received)

## Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+F   | Focus search input |
| Enter    | Find next match   |

## Troubleshooting

### Search finds nothing but text is visible

- Check "Match case" checkbox — it may be filtering out matches.
- Ensure the response body is plain text (search works on displayed content; JSON highlighting does
  not affect search).

### Match counter shows "No matches" after typing

- Search runs on every keystroke. For very large responses (100KB+), there may be a delay.
- See [60-tech-debt.md](../../ai-tasks/PYPOST-37/60-tech-debt.md) for performance notes.

### Ctrl+F does not focus search

- Verify focus is within `ResponseView` or its children. The shortcut is registered on the widget.
- If another widget has captured Ctrl+F, it may take precedence.

### Search metrics are missing

- Confirm metrics server is running (Settings → Metrics).
- Inspect `/metrics` for `gui_response_search_actions_total{source="...", has_matches="..."}`.
