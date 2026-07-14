# PYPOST-769: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/architecture_audit.md` | Replaced `## Prioritized Recommendations` Jira table with `## Follow-up Work` → PYPOST-684 `60-tech-debt.md` |
| `doc/dev/security_audit.md` | Replaced `## Prioritized Recommendations` Jira table with `## Follow-up Work` → PYPOST-685 `60-tech-debt.md` |

## Maintainer workflow

When adding or closing audit remediation tickets:

1. Update Jira links in the **parent audit** `ai-tasks/PYPOST-###/60-tech-debt.md` only.
2. Keep dev summaries (`doc/dev/*_audit.md`) with `## Follow-up Work` pointing to that file —
   no inline Jira tables in follow-up sections.
3. Key Findings tables may still reference resolved ticket IDs for traceability.

## Cross-links

- Parent audit: [PYPOST-690/60-tech-debt.md](../PYPOST-690/60-tech-debt.md) — R-P2-003
- Architecture debt: [PYPOST-684/60-tech-debt.md](../PYPOST-684/60-tech-debt.md)
- Security debt: [PYPOST-685/60-tech-debt.md](../PYPOST-685/60-tech-debt.md)
- Reference pattern: [observability_audit.md](../doc/dev/observability_audit.md) § Follow-up Work
