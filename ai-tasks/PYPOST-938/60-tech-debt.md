# PYPOST-938: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: churn assessed; **KEEP CURRENT STRATEGY** for 873-style
packaging doc locks with explicit HARDEN revisit triggers in
`doc/dev/testing.md`. PYPOST-922 contract suite green (7 targeted tests).

## Shortcuts Taken

- **KEEP instead of preemptive harden** — churn is low (lock module unchanged
  since PYPOST-922); hardening now would be over-engineering per critical
  analysis.
- **Resilience via documented criteria** rather than new lock machinery —
  satisfies “more resilient lock strategy without false failures.”
- **Full `make check` not re-run** — validated targeted 922/938 contract tests.

## Code Quality Issues

- None introduced. Substring locks remain the accepted trade-off until revisit
  triggers fire.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Doc tokens: PYPOST-922 attribution | Covered (unchanged) |
| Broader beyond golden framing | Covered (unchanged) |
| Primary packaging vs PYTEST_ARGS narrow | Covered (unchanged) |
| Makefile help/recipe 922 locks | Covered (unchanged) |
| Meta-lock on KEEP decision text | Not added — doc section is sufficient |
| Semantic / schema-based doc assert | Deferred until HARDEN triggers |

Timeout markers: module `pytestmark` unchanged. **No timeout-marker blockers.**

## Performance Concerns

None. Disk-read unit tests only.

## Follow-up Tasks

None. PYPOST-922 follow-up 3 is closed by this KEEP + criteria delivery.
Sibling optional harden for UI-actions packaging locks remains
[PYPOST-954](https://pypost.atlassian.net/browse/PYPOST-954) (separate surface).

## Blocker Verdict

**SAFE TO CLOSE** — no blockers relative to DoD.
