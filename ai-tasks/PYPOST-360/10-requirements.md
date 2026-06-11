# PYPOST-360: Close debt — guard against infinite match-index loop

## Goals

`_current_match_index` must not loop indefinitely when scanning matches in a large document.

## Definition of Done

1. A safety limit bounds the match-index scan loop.
2. Loop returns 0 when limit exceeded (intentional design).
3. Debt item traceable to `response_view.py`.

## Task Description

Verification-only closure. Safety limit is intentional design, not a bug.
