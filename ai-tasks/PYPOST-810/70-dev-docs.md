# PYPOST-810: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/licensing.md` | § Pre-binary-release legal review gate (G1–G8); § Platform-specific distribution notes (macOS, Windows, Linux); troubleshooting rows; title cites PYPOST-810 |
| `doc/dev/dependencies_audit.md` | License Notes cross-link to legal review gate anchor |

## Key maintainer workflow

1. Before the **first** official binary/installer, complete gate G1–G8 in
   [licensing.md](../../doc/dev/licensing.md#pre-binary-release-legal-review-gate-pypost-810).
2. Review per-platform Qt bundling notes for each target OS/format.
3. Regenerate `LICENSES/transitive.csv` and pass `make check-license-inventory` (G5).
4. Record exact PySide6/Qt/Python versions in release notes (G6).
5. After packaging tooling lands, re-run G2–G6 on version or layout changes.

## Cross-links

- Parent LGPL guide: [licensing.md](../../doc/dev/licensing.md) (PYPOST-786)
- Transitive inventory: [LICENSES/transitive.csv](../../LICENSES/transitive.csv) (PYPOST-809)
- Dependency audit: [dependencies_audit.md](../../doc/dev/dependencies_audit.md)
- PYPOST-786 follow-up origin: [ai-tasks/PYPOST-786/60-tech-debt.md](../PYPOST-786/60-tech-debt.md)

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-810 end-to-end, tokens_used: 45000
