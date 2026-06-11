# PYPOST-353: Close debt — debounce search on large documents

## Goals

Large-document search must not rescan the full body on every keystroke. Debounce typed
search input before running expensive match scans.

## Definition of Done

1. `SEARCH_DEBOUNCE_MS` constant (250 ms) gates search on large documents.
2. `test_large_document_debounces_search` verifies debounce behavior.
3. Debt item traceable to `response_view.py` and tests.

## Task Description

Verification-only closure. Debounce implemented in prior sprint work.
