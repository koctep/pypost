# PYPOST-123: Technical Debt Review

## Blockers

None — safe to close.

## Resolved

- **Multi-level tooltip chains** (PYPOST-13 follow-up): Plain `{{name}}` hover now follows
  chains with cycle detection and a depth bound.

## Remaining (non-blockers)

- **Values with embedded placeholders**: A value like `https://{{host}}/api` is not expanded
  on hover; only values that are exactly `{{name}}` participate in chaining.

## New follow-ups

None introduced by this change.

## Verdict

**SAFE TO CLOSE**
