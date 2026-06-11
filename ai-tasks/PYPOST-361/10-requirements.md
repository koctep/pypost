# PYPOST-361: Close debt — named constant for match-index safety limit

## Goals

Replace the magic number 10000 in the match-index scan loop with a named module-level
constant.

## Definition of Done

1. `MATCH_INDEX_SAFETY_LIMIT` exported at module level in `response_view.py`.
2. `_current_match_index` references the constant instead of a literal.

## Task Description

Verification-only closure. Constant added in parent sprint work.
