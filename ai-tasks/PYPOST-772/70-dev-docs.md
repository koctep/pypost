# PYPOST-772: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | Added `## ai-tasks artifact expectations` with standard, Code Audit, and legacy sections |

## Maintainer workflow

When closing a Jira task via the top-down workflow:

1. Create `ai-tasks/<JIRA-ID>/` and follow the file list in `doc/dev/setup.md`.
2. Always include `60-tech-debt.md` (Step 6) even when no debt remains — state explicitly.
3. For Code Audit tasks, add `30-audit-report.md` between architecture and code cleanup.
4. Run `python3 scripts/consolidate_tech_debt.py` after adding Jira-linked follow-ups
   (see [tech_debt_inventory.md](../doc/dev/tech_debt_inventory.md)).

## Cross-links

- Parent audit: [PYPOST-690/60-tech-debt.md](../PYPOST-690/60-tech-debt.md) — R-P2-006
- Artifact quality metrics: [doc/dev/documentation_audit.md](../doc/dev/documentation_audit.md)
- Roadmap template: [.cursor/templates/top-to-bottom/roadmap.md](../.cursor/templates/top-to-bottom/roadmap.md)
