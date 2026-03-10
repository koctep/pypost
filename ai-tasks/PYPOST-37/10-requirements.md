# PYPOST-37: Search in Response Window

## Goals

When viewing HTTP response bodies (especially large JSON or text), users need to quickly
find specific values or strings. Currently they must manually scroll and visually scan.
A text search feature reduces time spent locating information and improves productivity.

## User Stories

- As a user, I want to search for text in the response body so that I can quickly find
  specific values without manual scrolling.
- As a user, I want to navigate between search matches (next/previous) so that I can
  review all occurrences.
- As a user, I want to see whether there are matches and my current position (e.g.
  "3 of 5") so that I know the search result.

## Definition of Done

- Search input field is visible in or near the response area.
- User can enter search text and trigger search.
- All occurrences of the search string are found (plain text, case-sensitive or
  case-insensitive per user preference).
- User can jump to next/previous match.
- Search works when response body contains text (JSON, plain text, HTML, etc.).
- No matches: user receives clear feedback (e.g. "No matches").

## Task Description

**Scope:** The response window displays HTTP response body. Users view API responses,
often large JSON or text payloads, and need to locate specific values.

**Functional scope:**

- Add search UI: input field for search string.
- Plain text search only (no regex).
- Next/Previous navigation between matches.
- Optional: case sensitivity toggle.
- Optional: match counter (e.g. "2 of 5").

**Out of scope:** Regex search, search in request editor, search in headers.

**Programming language:** Python (PySide6/Qt) — consistent with existing PyPost
codebase.

## Q&A

- **Q:** Case sensitivity? **A:** Can be added as optional toggle; default
  case-insensitive is common.
- **Q:** Hotkey for search? **A:** Can be considered in implementation (e.g. Ctrl+F)
  if not conflicting with existing hotkeys.
