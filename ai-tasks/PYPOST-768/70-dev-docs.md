# PYPOST-768: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/solid_audit.md` | MainWindow Key Findings — PYPOST-43 resolved; cite `baseline-metrics.md`; sync regression table; PYPOST-768 verification note |

## Maintainer workflow

When MainWindow LOC or caps change via PYPOST-376:

1. Regenerate `ai-tasks/PYPOST-376/baseline-metrics.md` with `audit_baseline_metrics.py`.
2. Update the summary table in `solid_audit.md` **or** rely on the authoritative snapshot link
   only (prefer updating both when baseline columns change).
3. Add a dated verification note under Regression baseline metrics if closing a related debt
   ticket.

## Cross-links

- Parent audit: [solid_audit.md](../doc/dev/solid_audit.md), finding D-002 / R-P2-002
- Source task: [PYPOST-690/60-tech-debt.md](../PYPOST-690/60-tech-debt.md)
- Baseline snapshot: [PYPOST-376/baseline-metrics.md](../PYPOST-376/baseline-metrics.md)
- Resolved decomposition: [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43)
