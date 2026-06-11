# PYPOST-356: Close debt — ResponseView search unit tests

## Goals

ResponseView search behavior must have automated unit-level test coverage.

## Definition of Done

1. Unit tests cover search, navigation, debounce, and match capping.
2. Tests pass with headless Qt (`QT_QPA_PLATFORM=offscreen`).
3. Debt item traceable to `tests/test_response_view_search.py`.

## Task Description

Verification-only closure. Same test suite as PYPOST-352.
