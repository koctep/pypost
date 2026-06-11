# PYPOST-358: Close debt — cap match count on large documents

## Goals

Match counting on large documents must not scan unbounded matches; cap at a fixed limit
and show a capped indicator in the UI.

## Definition of Done

1. `MATCH_COUNT_CAP = 1000` limits match enumeration on large documents.
2. UI shows `1000+` style labels when capped.
3. `test_large_document_shows_capped_match_counter` verifies behavior.

## Task Description

Verification-only closure. Cap implemented in prior sprint work.
