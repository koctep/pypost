# PYPOST-768: Architecture

## Approach

Documentation-only change. No application code.

## Narrative structure

| Section | Change |
| --- | --- |
| Key Findings — MainWindow | Replace stale LOC parenthetical with resolved status + link to PYPOST-43 and `baseline-metrics.md` |
| Prioritized Recommendations P1 | Mark MainWindow decomposition **resolved** with Jira link |
| Regression baseline metrics table | Sync baseline columns to `baseline-metrics.md` (393 file / 353 class); add authoritative snapshot line |
| Verification note | Add PYPOST-768 closure entry (same pattern as PYPOST-728 / PYPOST-735) |

## Source of truth

`ai-tasks/PYPOST-376/baseline-metrics.md` — do not duplicate module inventory; link for full
table and regeneration commands.

## Files touched

| File | Change |
| --- | --- |
| `doc/dev/solid_audit.md` | MainWindow narrative refresh |

## Out of scope

- Regenerating `baseline-metrics.md` snapshot (no cap changes)
- Code Audit sibling footer standardization (PYPOST-767)
- `doc/dev/tech-debt/PYPOST-40.md` follow-up table (separate maintenance)
