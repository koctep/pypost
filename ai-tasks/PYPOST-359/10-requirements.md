# PYPOST-359: Close debt — avoid per-keystroke scans on large documents

## Goals

Typing in the search field on a large document must not trigger a full-body scan on every
keystroke.

## Definition of Done

1. Debounce defers search until typing pauses on large documents.
2. `test_large_document_debounces_search` verifies behavior.
3. Same resolution as PYPOST-353.

## Task Description

Verification-only closure. Addressed by search debounce (PYPOST-353).
