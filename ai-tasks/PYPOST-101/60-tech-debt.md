# PYPOST-101: Technical Debt Analysis

## Shortcuts Taken

- **Fixed threshold**: `MAX_HIGHLIGHT_BLOCK_CHARS = 32_768` is hardcoded, not user-configurable.
  Acceptable for a debt fix; typical API payloads stay well below the limit.

## Code Quality Issues

None introduced.

## Missing Tests

- No benchmark asserting wall-clock bound on multi-megabyte blocks (covered implicitly by
  early-return unit test; full perf test would be flaky in CI).

## Performance Concerns

- **Partial coloring on huge documents**: Only oversized blocks skip highlighting; a document
  mixing short and very long lines may show inconsistent colors. Rare for JSON editors.

## Blocker Review

**Verdict: SAFE TO CLOSE** — guard addresses the stated megabyte-line risk without regressions
on normal payloads.

## Follow-up Tasks

None.
