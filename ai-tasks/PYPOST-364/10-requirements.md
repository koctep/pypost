# PYPOST-364: Capped match count for large response search

## Goals

Response body search in PyPost counts every match to show a counter such as "2 of 5". For large
HTTP responses (over 100KB), scanning the entire document on each keystroke makes search feel slow
and unresponsive. Users searching large API payloads need the same search experience without
noticeable lag.

## User Stories

- As an API developer, when I search a response body larger than 100KB, I want the match counter
  to update quickly so I can navigate results without waiting on a full document scan.
- As an API developer, when a large response has very many matches, I want the counter to indicate
  that the total is approximate (for example "2 of 1000+") so I still know my position without
  requiring an exact total.
- As an API developer, when a large response has only a few matches, I want an exact counter
  (for example "1 of 3") so navigation remains precise.

## Definition of Done

- Match counting for response bodies over 100KB does not scan the entire document when matches
  exceed a reasonable cap.
- The status label shows an approximate total with a "+" suffix when the cap is reached.
- Small response bodies (100KB or less) keep exact match counting and existing label formats.
- Existing search behaviour (find next/previous, case sensitivity, metrics) is unchanged.
- Automated tests cover capped and exact counting for large documents.

## Task Description

Follow-up to PYPOST-37 response search. The current implementation walks the full document in
`_count_matches()` on every search update. For documents above 100KB, apply a capped count so
scanning stops after a maximum number of matches and the UI shows "N of M+" when more matches
may exist.

## Q&A

- **Q:** What threshold defines a "large" document? **A:** 100KB of displayed body text, as noted
  in PYPOST-37 technical debt.
- **Q:** Should navigation (next/previous) change? **A:** No — only how the total match count is
  computed and displayed.
